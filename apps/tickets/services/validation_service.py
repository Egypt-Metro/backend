from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Dict

from apps.tickets.constants.choices import TicketChoices
from apps.tickets.services.hardware_service import HardwareService
from ..models.ticket import Ticket
from .qr_service import QRService
from apps.routes.services.route_service import MetroRouteService


class ValidationService:
    route_service = MetroRouteService()
    qr_service = QRService()
    hardware_service = HardwareService()

    @classmethod
    @transaction.atomic
    def validate_entry(cls, ticket_number: str, station_id: int) -> Dict:
        """
        Validate ticket at entry gate and sends result to hardware
        """
        if not isinstance(station_id, int) or station_id <= 0:
            raise ValidationError("Invalid station ID")

        try:
            ticket = Ticket.objects.select_for_update().get(
                ticket_number=ticket_number,
                status='ACTIVE'
            )

            # Expiration validation
            if ticket.valid_until < timezone.now():
                ticket.status = 'EXPIRED'
                ticket.save(update_fields=['status'])
                cls.hardware_service.send_validation_result(False)
                return {
                    'is_valid': False,
                    'message': 'Ticket has expired'
                }

            if ticket.entry_station_id:
                cls.hardware_service.send_validation_result(False)
                return {
                    'is_valid': False,
                    'message': 'Ticket already used for entry'
                }

            # Record entry
            ticket.entry_station_id = station_id
            ticket.entry_time = timezone.now()
            ticket.status = 'IN_USE'
            ticket.save()

            # Send success to hardware
            cls.hardware_service.send_validation_result(True)

            return {
                'is_valid': True,
                'message': 'Entry authorized',
                'ticket_number': ticket.ticket_number,
                'entry_time': ticket.entry_time
            }

        except Ticket.DoesNotExist:
            cls.hardware_service.send_validation_result(False)
            return {
                'is_valid': False,
                'message': 'Invalid ticket'
            }

    @classmethod
    @transaction.atomic
    def validate_exit(cls, ticket_number: str, station_id: int) -> Dict:
        """
        Validate ticket at exit gate and sends result to hardware
        """
        if not isinstance(station_id, int) or station_id <= 0:
            raise ValidationError("Invalid station ID")

        try:
            ticket = Ticket.objects.select_for_update().get(
                ticket_number=ticket_number,
                status='IN_USE'
            )

            if not ticket.entry_station_id:
                cls.hardware_service.send_validation_result(False)
                return {
                    'is_valid': False,
                    'message': 'No entry station recorded'
                }

            # Validate route
            route_data = cls.route_service.find_route(
                ticket.entry_station_id,
                station_id
            )

            if not route_data:
                cls.hardware_service.send_validation_result(False)
                return {
                    'is_valid': False,
                    'message': 'Invalid route'
                }

            # Check if route is within ticket's limit
            stations_count = route_data['num_stations']

            if stations_count > ticket.max_stations:
                try:
                    # Find next suitable ticket type
                    next_ticket = TicketChoices.get_next_ticket_type(stations_count)

                    if next_ticket:
                        # Set needs_upgrade flag and temporary exit station
                        ticket.needs_upgrade = True
                        ticket.temp_exit_station_id = station_id
                        ticket.save(update_fields=['needs_upgrade', 'temp_exit_station_id'])

                        # Handle different return types (could be dict or tuple)
                        if isinstance(next_ticket, tuple) and len(next_ticket) == 2:
                            next_ticket_type, next_ticket_details = next_ticket
                            price_difference = next_ticket_details['price'] - ticket.price
                            new_ticket_type_name = next_ticket_type
                        else:
                            # Assuming it's a dictionary
                            price_difference = next_ticket['price'] - ticket.price
                            new_ticket_type_name = next_ticket['name']

                        cls.hardware_service.send_validation_result(False)
                        return {
                            'is_valid': False,
                            'message': 'Ticket needs upgrade',
                            'needs_upgrade': True,
                            'upgrade_price': price_difference,
                            'new_ticket_type': new_ticket_type_name,
                            'stations_count': stations_count,
                            'max_stations': ticket.max_stations,
                            'redirect_to_metro_app': True
                        }
                    else:
                        cls.hardware_service.send_validation_result(False)
                        return {
                            'is_valid': False,
                            'message': 'Route exceeds maximum allowed stations and no upgrade available'
                        }
                except Exception as e:
                    # Log the exception for debugging
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error processing ticket upgrade: {str(e)}")

                    cls.hardware_service.send_validation_result(False)
                    return {
                        'is_valid': False,
                        'message': 'Unable to process ticket upgrade'
                    }

            # Record exit
            ticket.exit_station_id = station_id
            ticket.exit_time = timezone.now()
            ticket.status = 'USED'
            ticket.save()

            # Send success to hardware
            cls.hardware_service.send_validation_result(True)

            return {
                'is_valid': True,
                'message': 'Exit authorized',
                'ticket_number': ticket.ticket_number,
                'exit_time': ticket.exit_time,
                'total_stations': stations_count
            }

        except Ticket.DoesNotExist:
            cls.hardware_service.send_validation_result(False)
            return {
                'is_valid': False,
                'message': 'Invalid ticket'
            }

    @classmethod
    def verify_qr(cls, ticket_number: str, qr_data: str) -> Dict:
        """
        Verify QR code data and validate ticket
        """
        try:
            ticket = Ticket.objects.get(ticket_number=ticket_number)
            is_valid, result = cls.qr_service.validate_qr(qr_data, ticket.validation_hash)

            if not is_valid:
                return {
                    'is_valid': False,
                    'message': result.get('error', 'Invalid QR code')
                }

            # Additional validations
            if ticket.status == 'EXPIRED':
                return {
                    'is_valid': False,
                    'message': 'Ticket has expired'
                }

            if ticket.status == 'USED':
                return {
                    'is_valid': False,
                    'message': 'Ticket has already been used'
                }

            return {
                'is_valid': True,
                'message': 'Valid QR code',
                'ticket_data': {
                    'ticket_number': ticket.ticket_number,
                    'status': ticket.status,
                    'entry_station': ticket.entry_station.name if ticket.entry_station else None,
                    'valid_until': ticket.valid_until.isoformat()
                }
            }

        except Ticket.DoesNotExist:
            return {
                'is_valid': False,
                'message': 'Invalid ticket'
            }

    @classmethod
    def validate_route(cls, ticket: Ticket, station_id: int) -> Dict:
        """
        Validate route and calculate upgrade requirements if needed
        """
        route_data = cls.route_service.find_route(
            ticket.entry_station_id,
            station_id
        )

        if not route_data:
            return {
                'is_valid': False,
                'message': 'Invalid route'
            }

        stations_count = route_data['num_stations']

        if stations_count > ticket.max_stations:
            next_type, next_details = TicketChoices.get_next_ticket_type(stations_count)

            if next_type:
                price_difference = next_details['price'] - ticket.price
                return {
                    'is_valid': False,
                    'message': 'Ticket needs upgrade',
                    'needs_upgrade': True,
                    'upgrade_price': price_difference,
                    'stations_count': stations_count,
                    'current_type': ticket.ticket_type,
                    'next_type': next_type,
                    'next_max_stations': next_details['max_stations'],
                    'route': route_data
                }

            return {
                'is_valid': False,
                'message': 'Route exceeds maximum allowed stations'
            }

        return {
            'is_valid': True,
            'message': 'Valid route',
            'stations_count': stations_count,
            'route': route_data
        }
