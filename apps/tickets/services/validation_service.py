from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from typing import Dict
from ..models.ticket import Ticket
from .qr_service import QRService
from apps.routes.services.route_service import MetroRouteService
from ..utils.price_calculator import calculate_ticket_price


class ValidationService:
    route_service = MetroRouteService()
    qr_service = QRService()

    @classmethod
    @transaction.atomic
    def validate_entry(cls, ticket_number: str, station_id: int) -> Dict:
        """
        Validate ticket at entry gate
        Raises ValidationError if station_id is invalid
        """
        if not isinstance(station_id, int) or station_id <= 0:
            raise ValidationError("Invalid station ID")

        try:
            ticket = Ticket.objects.select_for_update().get(
                ticket_number=ticket_number
            )

            # Status validation
            if ticket.status != 'ACTIVE':
                return {
                    'is_valid': False,
                    'message': f'Ticket is {ticket.status.lower()}'
                }

            # Expiration validation
            if ticket.valid_until < timezone.now():
                ticket.status = 'EXPIRED'
                ticket.save(update_fields=['status'])
                return {
                    'is_valid': False,
                    'message': 'Ticket has expired'
                }

            # Station validation
            if ticket.entry_station_id != station_id:
                return {
                    'is_valid': False,
                    'message': 'Invalid entry station'
                }

            # Record entry
            ticket.entry_time = timezone.now()
            ticket.status = 'IN_USE'
            ticket.save(update_fields=['entry_time', 'status'])

            return {
                'is_valid': True,
                'message': 'Entry authorized',
                'ticket_number': ticket.ticket_number,
                'entry_time': ticket.entry_time
            }

        except Ticket.DoesNotExist:
            return {
                'is_valid': False,
                'message': 'Invalid ticket'
            }

    @classmethod
    @transaction.atomic
    def validate_exit(cls, ticket_number: str, station_id: int) -> Dict:
        """
        Validate ticket at exit gate
        Raises ValidationError if station_id is invalid
        """
        if not isinstance(station_id, int) or station_id <= 0:
            raise ValidationError("Invalid station ID")

        try:
            ticket = Ticket.objects.select_for_update().get(
                ticket_number=ticket_number,
                status='IN_USE'
            )

            # Validate route
            route_data = cls.route_service.find_route(
                ticket.entry_station_id,
                station_id
            )

            if not route_data:
                return {
                    'is_valid': False,
                    'message': 'Invalid route'
                }

            # Check stations count
            stations_count = route_data['num_stations']
            max_stations = int(ticket.price_category.split('_')[0])

            if stations_count > max_stations:
                new_price, new_category = calculate_ticket_price(stations_count)
                price_difference = new_price - ticket.price

                return {
                    'is_valid': False,
                    'message': 'Ticket needs upgrade',
                    'upgrade_required': True,
                    'upgrade_price': price_difference,
                    'stations_count': stations_count,
                    'current_category': ticket.price_category,
                    'new_category': new_category
                }

            # Record exit
            ticket.exit_station_id = station_id
            ticket.exit_time = timezone.now()
            ticket.status = 'USED'
            ticket.save(update_fields=['exit_station_id', 'exit_time', 'status'])

            return {
                'is_valid': True,
                'message': 'Exit authorized',
                'ticket_number': ticket.ticket_number,
                'exit_time': ticket.exit_time,
                'total_stations': stations_count
            }

        except Ticket.DoesNotExist:
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
        max_stations = int(ticket.price_category.split('_')[0])

        if stations_count > max_stations:
            new_price, new_category = calculate_ticket_price(stations_count)
            price_difference = new_price - ticket.price

            return {
                'is_valid': False,
                'message': 'Ticket needs upgrade',
                'upgrade_required': True,
                'upgrade_price': price_difference,
                'stations_count': stations_count,
                'current_category': ticket.price_category,
                'new_category': new_category,
                'route': route_data
            }

        return {
            'is_valid': True,
            'message': 'Valid route',
            'stations_count': stations_count,
            'route': route_data
        }
