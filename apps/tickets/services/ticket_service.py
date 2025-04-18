from datetime import timedelta
from typing import Dict, Optional, Tuple
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError

from ..models import Ticket
from ..utils.price_calculator import calculate_ticket_price
from .qr_service import QRService
from apps.stations.models import Station
from apps.routes.services.route_service import MetroRouteService


class TicketService:
    def __init__(self):
        self.route_service = MetroRouteService()
        self.qr_service = QRService()

    @transaction.atomic
    def create_ticket(
        self,
        user,
        entry_station_id: int,
        exit_station_id: Optional[int] = None
    ) -> Ticket:
        """
        Creates a new ticket with calculated price based on route

        Args:
            user: User creating the ticket
            entry_station_id: ID of entry station
            exit_station_id: Optional ID of exit station

        Returns:
            Created Ticket instance

        Raises:
            ValidationError: If station IDs are invalid or no valid route exists
        """
        # Add validation for station IDs
        if not isinstance(entry_station_id, int) or entry_station_id <= 0:
            raise ValidationError("Invalid entry station ID")
        if exit_station_id and (not isinstance(exit_station_id, int) or exit_station_id <= 0):
            raise ValidationError("Invalid exit station ID")

        try:
            entry_station = Station.objects.get(id=entry_station_id)
        except Station.DoesNotExist:
            raise ValidationError("Entry station not found")

        exit_station = None
        route_data = None

        if exit_station_id:
            try:
                exit_station = Station.objects.get(id=exit_station_id)
                route_data = self.route_service.find_route(entry_station_id, exit_station_id)

                if not route_data:
                    raise ValidationError("No valid route found between stations")
            except Station.DoesNotExist:
                raise ValidationError("Exit station not found")

        # Calculate initial price and category
        stations_count = route_data['num_stations'] if route_data else 9
        price, category = calculate_ticket_price(stations_count)

        # Create ticket
        ticket = Ticket.objects.create(
            user=user,
            entry_station=entry_station,
            exit_station=exit_station,
            ticket_type='SINGLE',
            price_category=category,
            price=price,
            status='ACTIVE',
            valid_until=timezone.now() + timedelta(days=1)
        )

        # Generate QR code data
        ticket_data = {
            'id': ticket.id,
            'ticket_number': ticket.ticket_number,
            'user_id': user.id,
            'entry_station': entry_station.name,
            'exit_station': exit_station.name if exit_station else None,
            'created_at': ticket.created_at.isoformat(),
            'valid_until': ticket.valid_until.isoformat()
        }

        # Generate and save QR code
        qr_code, validation_hash = self.qr_service.generate_ticket_qr(ticket_data)
        ticket.qr_code = qr_code
        ticket.validation_hash = validation_hash
        ticket.save(update_fields=['qr_code', 'validation_hash'])

        return ticket

    @transaction.atomic
    def validate_entry(self, ticket_number: str, station_id: int) -> Dict:
        """Validates ticket at entry gate"""
        try:
            ticket = Ticket.objects.select_for_update().get(
                ticket_number=ticket_number,
                status='ACTIVE'
            )

            if ticket.valid_until < timezone.now():
                ticket.status = 'EXPIRED'
                ticket.save()
                return {
                    'is_valid': False,
                    'message': 'Ticket has expired'
                }

            if ticket.entry_station_id != station_id:
                return {
                    'is_valid': False,
                    'message': 'Invalid entry station'
                }

            ticket.entry_time = timezone.now()
            ticket.status = 'IN_USE'
            ticket.save()

            return {
                'is_valid': True,
                'message': 'Entry authorized'
            }

        except Ticket.DoesNotExist:
            return {
                'is_valid': False,
                'message': 'Invalid ticket'
            }

    @transaction.atomic
    def validate_exit(self, ticket_number: str, station_id: int) -> Dict:
        """Validates ticket at exit gate"""
        try:
            ticket = Ticket.objects.select_for_update().get(
                ticket_number=ticket_number,
                status='IN_USE'
            )

            # Get actual route taken
            actual_route = self.route_service.find_route(
                ticket.entry_station_id,
                station_id
            )

            if not actual_route:
                return {
                    'is_valid': False,
                    'message': 'Invalid route'
                }

            # Check if route is within ticket's limit
            stations_count = actual_route['num_stations']
            max_stations = int(ticket.price_category.split('_')[0])

            if stations_count > max_stations:
                new_price, _ = calculate_ticket_price(stations_count)
                price_difference = new_price - ticket.price

                return {
                    'is_valid': False,
                    'message': 'Ticket needs upgrade',
                    'upgrade_required': True,
                    'upgrade_price': price_difference,
                    'stations_count': stations_count
                }

            # Valid exit
            ticket.exit_station_id = station_id
            ticket.exit_time = timezone.now()
            ticket.status = 'USED'
            ticket.save()

            return {
                'is_valid': True,
                'message': 'Exit authorized'
            }

        except Ticket.DoesNotExist:
            return {
                'is_valid': False,
                'message': 'Invalid ticket'
            }

    def upgrade_ticket(
        self,
        ticket_number: str,
        new_station_count: int,
        payment_confirmed: bool = False
    ) -> Tuple[bool, Dict]:
        """
        Upgrades a ticket to cover more stations
        """
        if not payment_confirmed:
            return False, {'message': 'Payment required for upgrade'}

        with transaction.atomic():
            ticket = Ticket.objects.select_for_update().get(
                ticket_number=ticket_number
            )

            new_price, new_category = calculate_ticket_price(new_station_count)

            # Update ticket
            ticket.price = new_price
            ticket.price_category = new_category
            ticket.status = 'ACTIVE'
            ticket.save()

            return True, {
                'message': 'Ticket upgraded successfully',
                'new_price': new_price,
                'new_category': new_category
            }
