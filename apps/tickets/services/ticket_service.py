from datetime import timedelta
from typing import Dict, Tuple
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError

from ..models import Ticket
from ..constants.choices import TicketChoices
from .qr_service import QRService
from apps.routes.services.route_service import MetroRouteService


class TicketService:
    def __init__(self):
        self.route_service = MetroRouteService()
        self.qr_service = QRService()

    @transaction.atomic
    def create_ticket(
        self,
        user,
        ticket_type: str,
        quantity: int = 1
    ) -> Ticket:
        if quantity < 1:
            raise ValidationError("Quantity must be at least 1")

        ticket_details = TicketChoices.TICKET_TYPES.get(ticket_type)
        if not ticket_details:
            raise ValidationError("Invalid ticket type")

        # Don't generate token here - it will be generated in qr_service.py

        tickets = []
        for _ in range(quantity):
            # Create ticket with initial values
            ticket = Ticket.objects.create(
                user=user,
                ticket_type=ticket_type,
                price=ticket_details['price'],
                status='ACTIVE',
                color=ticket_details['color'],
                max_stations=ticket_details['max_stations'],
                valid_until=timezone.now() + timedelta(days=1)
            )

            # Generate QR code data
            ticket_data = {
                'id': ticket.id,
                'ticket_number': ticket.ticket_number,
                'user_id': user.id,
                'ticket_type': ticket_type,
                'created_at': ticket.created_at.isoformat(),
                'valid_until': ticket.valid_until.isoformat(),
            }

            # Generate and save QR code
            qr_code, validation_hash = self.qr_service.generate_ticket_qr(ticket_data)
            ticket.qr_code = qr_code
            ticket.validation_hash = validation_hash
            ticket.save(update_fields=['qr_code', 'validation_hash'])

            tickets.append(ticket)

        return tickets if quantity > 1 else tickets[0]

    @transaction.atomic
    def validate_entry(self, ticket_number: str, station_id: int) -> Dict:
        """Validates ticket at entry gate and records start station"""
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

            if ticket.entry_station_id:
                return {
                    'is_valid': False,
                    'message': 'Ticket already used for entry'
                }

            # Record entry station and time
            ticket.entry_station_id = station_id
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
        """Validates ticket at exit gate and handles potential upgrades"""
        try:
            ticket = Ticket.objects.select_for_update().get(
                ticket_number=ticket_number,
                status='IN_USE'
            )

            if not ticket.entry_station_id:
                return {
                    'is_valid': False,
                    'message': 'No entry station recorded'
                }

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

            if stations_count > ticket.max_stations:
                # Find next suitable ticket type
                next_ticket = TicketChoices.get_next_ticket_type(stations_count)

                if next_ticket:
                    price_difference = next_ticket['price'] - ticket.price
                    ticket.upgrade_required = True
                    ticket.test_exit_station_id = station_id
                    ticket.save(update_fields=['upgrade_required', 'test_exit_station_id'])
                    return {
                        'is_valid': False,
                        'upgrade_required': True,
                        'stations_count': stations_count,
                        'max_stations': ticket.max_stations,
                        'new_ticket_type': next_ticket['name'],
                        'upgrade_price': price_difference,
                        'stations_count': stations_count,
                        'message': 'Ticket needs upgrade'
                    }
                return {
                    'is_valid': False,
                    'message': 'Route exceeds maximum allowed stations'
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

    @transaction.atomic
    def upgrade_ticket(
        self,
        ticket_number: str,
        new_ticket_type: str,
        payment_confirmed: bool = False
    ) -> Tuple[bool, Dict]:
        """
        Upgrades a ticket to a higher type
        """
        if not payment_confirmed:
            return False, {'message': 'Payment required for upgrade'}

        try:
            ticket = Ticket.objects.select_for_update().get(
                ticket_number=ticket_number
            )

            new_ticket_details = TicketChoices.TICKET_TYPES.get(new_ticket_type)
            if not new_ticket_details:
                return False, {'message': 'Invalid ticket type for upgrade'}

            # Update ticket with new type details
            ticket.price = new_ticket_details['price']
            ticket.price_category = new_ticket_details['category']
            ticket.color = new_ticket_details['color']
            ticket.max_stations = new_ticket_details['max_stations']
            ticket.status = 'ACTIVE'
            ticket.upgrade_required = False
            ticket.save(update_fields=[
                'price',
                'price_category',
                'color',
                'max_stations',
                'status',
                'upgrade_required'
            ])

            return True, {
                'message': 'Ticket upgraded successfully',
                'new_ticket_type': new_ticket_type,
                'new_price': new_ticket_details['price']
            }

        except Ticket.DoesNotExist:
            return False, {'message': 'Ticket not found'}
