# apps/trains/services/ai_service.py

from datetime import timezone
import logging
import aiohttp
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class AIService:
    """
    Service to interact with external AI model API
    This service acts as a bridge between your backend and the AI model service
    """

    def __init__(self):
        self.api_base_url = settings.AI_SERVICE_URL
        self.api_key = settings.AI_SERVICE_API_KEY
        self.cache_timeout = 300  # 5 minutes

    async def process_camera_feed(self, camera_id, image_data):
        """Process camera feed through external AI service"""
        try:
            cache_key = f'camera_processing_{camera_id}'

            # Check cache first
            cached_result = cache.get(cache_key)
            if cached_result:
                return cached_result

            # Prepare the request to the AI service
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }

            payload = {
                'camera_id': camera_id,
                'image_data': image_data,
                'timestamp': timezone.now().isoformat()
            }

            # Make request to AI service
            response = await self._make_api_request(
                endpoint='/process-crowd',
                method='POST',
                data=payload,
                headers=headers
            )

            if response and response.get('success'):
                result = {
                    'passenger_count': response['passenger_count'],
                    'confidence_score': response['confidence_score'],
                    'timestamp': response['timestamp']
                }
                cache.set(cache_key, result, self.cache_timeout)
                return result

            return None

        except Exception as e:
            logger.error(f"Error processing camera feed: {e}")
            return None

    async def get_crowd_prediction(self, train_car_id, timestamp):
        """Get crowd prediction from AI service"""
        try:
            cache_key = f'crowd_prediction_{train_car_id}_{timestamp}'

            # Check cache
            cached_prediction = cache.get(cache_key)
            if cached_prediction:
                return cached_prediction

            # Request prediction from AI service
            response = await self._make_api_request(
                endpoint='/predict-crowd',
                method='GET',
                params={
                    'train_car_id': train_car_id,
                    'timestamp': timestamp.isoformat()
                }
            )

            if response and response.get('success'):
                prediction = {
                    'predicted_count': response['predicted_count'],
                    'confidence': response['confidence'],
                    'factors': response.get('factors', [])
                }
                cache.set(cache_key, prediction, self.cache_timeout)
                return prediction

            return None

        except Exception as e:
            logger.error(f"Error getting crowd prediction: {e}")
            return None

    async def _make_api_request(self, endpoint, method='GET', data=None, params=None, headers=None):
        """Make request to AI service API"""
        try:
            url = f"{self.api_base_url}{endpoint}"

            async with aiohttp.ClientSession() as session:
                if method == 'GET':
                    async with session.get(url, params=params, headers=headers) as response:
                        return await response.json()
                elif method == 'POST':
                    async with session.post(url, json=data, headers=headers) as response:
                        return await response.json()

        except Exception as e:
            logger.error(f"API request error: {e}")
            return None
