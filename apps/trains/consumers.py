# apps/trains/consumers.py

import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.exceptions import DenyConnection
from channels.db import database_sync_to_async
from .services.train_service import TrainService
from .models import Train

logger = logging.getLogger(__name__)


class TrainConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time train updates.
    Handles:
    - Live train location updates
    - Crowd level updates
    - Schedule changes/delays
    - Service alerts
    """

    async def connect(self):
        """Handle WebSocket connection and authentication"""
        try:
            # Get train ID from URL route
            self.train_id = self.scope['url_route']['kwargs']['train_id']

            # Verify train exists
            train_exists = await self.verify_train()
            if not train_exists:
                logger.warning(f"Attempted connection to non-existent train: {self.train_id}")
                raise DenyConnection()

            # Set up group names for different update types
            self.base_group = f'train_{self.train_id}'
            self.location_group = f'{self.base_group}_location'
            self.crowd_group = f'{self.base_group}_crowd'
            self.schedule_group = f'{self.base_group}_schedule'

            # Join all relevant groups
            for group in [self.base_group, self.location_group, self.crowd_group, self.schedule_group]:
                await self.channel_layer.group_add(group, self.channel_name)

            await self.accept()

            # Send initial data
            await self.send_initial_data()
            logger.info(f"WebSocket connection established for train: {self.train_id}")

        except DenyConnection:
            raise
        except Exception as e:
            logger.error(f"Error establishing WebSocket connection: {e}")
            raise DenyConnection()

    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        try:
            # Leave all groups
            for group in [self.base_group, self.location_group, self.crowd_group, self.schedule_group]:
                await self.channel_layer.group_discard(group, self.channel_name)

            logger.info(f"WebSocket connection closed for train: {self.train_id}")
        except Exception as e:
            logger.error(f"Error during WebSocket disconnection: {e}")

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            message_data = data.get('data', {})

            # Handle different types of updates
            handlers = {
                'location_update': self.handle_location_update,
                'crowd_update': self.handle_crowd_update,
                'schedule_update': self.handle_schedule_update,
                'service_alert': self.handle_service_alert,
                'request_status': self.handle_status_request
            }

            handler = handlers.get(message_type)
            if handler:
                await handler(message_data)
            else:
                logger.warning(f"Unknown message type received: {message_type}")

        except json.JSONDecodeError:
            logger.error("Invalid JSON received")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self.send_error("Error processing message")

    @database_sync_to_async
    def verify_train(self):
        """Verify train exists in database"""
        try:
            return Train.objects.filter(train_id=self.train_id).exists()
        except Exception:
            return False

    async def send_initial_data(self):
        """Send initial train status data"""
        try:
            train_service = TrainService()
            status = await database_sync_to_async(train_service.get_train_status)(self.train_id)

            if status:
                await self.send(text_data=json.dumps({
                    'type': 'initial_data',
                    'data': status
                }))
        except Exception as e:
            logger.error(f"Error sending initial data: {e}")
            await self.send_error("Error fetching initial data")

    async def handle_location_update(self, data):
        """Handle train location updates"""
        try:
            # Validate location data
            if self.validate_location_data(data):
                await self.channel_layer.group_send(
                    self.location_group,
                    {
                        'type': 'location_update',
                        'data': {
                            'train_id': self.train_id,
                            'latitude': data['latitude'],
                            'longitude': data['longitude'],
                            'speed': data.get('speed'),
                            'timestamp': data.get('timestamp')
                        }
                    }
                )
        except Exception as e:
            logger.error(f"Error handling location update: {e}")
            await self.send_error("Error updating location")

    async def handle_crowd_update(self, data):
        """Handle crowd level updates"""
        try:
            # This will be integrated with AI model later
            await self.channel_layer.group_send(
                self.crowd_group,
                {
                    'type': 'crowd_update',
                    'data': {
                        'train_id': self.train_id,
                        'car_number': data.get('car_number'),
                        'passenger_count': data.get('passenger_count'),
                        'timestamp': data.get('timestamp')
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error handling crowd update: {e}")
            await self.send_error("Error updating crowd data")

    async def handle_schedule_update(self, data):
        """Handle schedule updates"""
        try:
            await self.channel_layer.group_send(
                self.schedule_group,
                {
                    'type': 'schedule_update',
                    'data': {
                        'train_id': self.train_id,
                        'status': data.get('status'),
                        'delay': data.get('delay'),
                        'next_station': data.get('next_station'),
                        'estimated_arrival': data.get('estimated_arrival')
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error handling schedule update: {e}")
            await self.send_error("Error updating schedule")

    async def handle_service_alert(self, data):
        """Handle service alerts"""
        try:
            await self.channel_layer.group_send(
                self.base_group,
                {
                    'type': 'service_alert',
                    'data': {
                        'train_id': self.train_id,
                        'alert_type': data.get('alert_type'),
                        'message': data.get('message'),
                        'severity': data.get('severity', 'info')
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error handling service alert: {e}")
            await self.send_error("Error sending service alert")

    async def handle_status_request(self, data):
        """Handle requests for current train status"""
        try:
            train_service = TrainService()
            status = await database_sync_to_async(train_service.get_train_status)(self.train_id)

            if status:
                await self.send(text_data=json.dumps({
                    'type': 'status_update',
                    'data': status
                }))
        except Exception as e:
            logger.error(f"Error handling status request: {e}")
            await self.send_error("Error fetching status")

    # Message type handlers
    async def location_update(self, event):
        """Send location update to WebSocket"""
        await self.send(text_data=json.dumps(event['data']))

    async def crowd_update(self, event):
        """Send crowd update to WebSocket"""
        await self.send(text_data=json.dumps(event['data']))

    async def schedule_update(self, event):
        """Send schedule update to WebSocket"""
        await self.send(text_data=json.dumps(event['data']))

    async def service_alert(self, event):
        """Send service alert to WebSocket"""
        await self.send(text_data=json.dumps(event['data']))

    async def send_error(self, message):
        """Send error message to WebSocket"""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': message
        }))

    @staticmethod
    def validate_location_data(data):
        """Validate location update data"""
        required_fields = ['latitude', 'longitude']
        return all(field in data for field in required_fields)
