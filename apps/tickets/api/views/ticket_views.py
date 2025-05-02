from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError
from django.db import transaction, models
from django.utils import timezone

from apps.tickets.constants.choices import TicketChoices
from ..serializers.ticket_serializers import (
    TicketSerializer,
)
from ...models.ticket import Ticket
from ...services.ticket_service import TicketService
from ...services.validation_service import ValidationService
from .wallet_integration import WalletTicketMixin


class TicketViewSet(WalletTicketMixin, viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [AllowAny]
    ticket_service = TicketService()
    http_method_names = ['get', 'post', 'patch']
    queryset = Ticket.objects.none()

    def get_queryset(self):
        """Get and filter tickets for the current user with automatic expiry handling"""
        # Get current time
        now = timezone.now()
        # Get base queryset for the current user
        queryset = Ticket.objects.filter(user=self.request.user)
        # Update expired tickets (do this first to ensure accurate status)
        expired_tickets = queryset.filter(
            valid_until__lt=now,
            status='ACTIVE'
        )
        if expired_tickets.exists():
            expired_tickets.update(status='EXPIRED')
        # Get status filter from request params
        status = self.request.query_params.get('status', None)
        # Apply status filtering
        if status and status.upper() != 'ALL':
            queryset = queryset.filter(status=status.upper())
        elif not status:
            # By default, show active and in-use tickets
            queryset = queryset.filter(status__in=['ACTIVE', 'IN_USE'])
        return queryset.order_by('-created_at')

    @action(detail=False, methods=['get'], url_path='sync')
    def sync_tickets(self, request):
        """
        Sync tickets after login - retrieves active and in-use tickets
        """
        now = timezone.now()

        # Get user's valid tickets (active or in-use)
        valid_tickets = Ticket.objects.filter(
            user=request.user
        ).filter(
            models.Q(status='ACTIVE', valid_until__gte=now)
            | models.Q(status='IN_USE')
        ).select_related('entry_station', 'exit_station').order_by('-created_at')

        return Response({
            "success": True,
            "data": self.get_serializer(valid_tickets, many=True).data,
            "count": valid_tickets.count(),
            "message": f"Successfully synced {valid_tickets.count()} tickets"
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='dashboard')
    def dashboard(self, request):
        """Get user's ticket dashboard summary"""
        now = timezone.now()

        # Active tickets (valid and not used)
        active_tickets = Ticket.objects.filter(
            user=request.user,
            status='ACTIVE',
            valid_until__gte=now
        ).order_by('-created_at')

        # In-use tickets (entered but not exited)
        in_use_tickets = Ticket.objects.filter(
            user=request.user,
            status='IN_USE'
        )

        # Recent used tickets
        recent_used = Ticket.objects.filter(
            user=request.user,
            status='USED',
            exit_time__gte=now - timezone.timedelta(days=7)
        ).order_by('-exit_time')[:5]
        return Response({
            "success": True,
            "data": {
                "active_tickets": self.get_serializer(active_tickets, many=True).data,
                "in_use_tickets": self.get_serializer(in_use_tickets, many=True).data,
                "recent_used": self.get_serializer(recent_used, many=True).data,
                "active_count": active_tickets.count(),
                "in_use_count": in_use_tickets.count()
            },
            "message": "User tickets dashboard retrieved successfully"
        })

    @action(detail=False, methods=['get'], url_path='types')
    def types(self, request):
        """Get ticket types"""
        return Response({
            "success": True,
            "data": TicketChoices.TICKET_TYPES,
            "message": "Ticket types retrieved successfully"
        })

    @transaction.atomic
    def create(self, request):
        """Create new ticket(s)"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            try:
                tickets = self.ticket_service.create_ticket(
                    user=request.user,
                    ticket_type=serializer.validated_data['ticket_type'],
                    quantity=serializer.validated_data.get('quantity', 1)
                )

                # Convert single ticket to list for consistent serialization
                tickets_list = tickets if isinstance(tickets, list) else [tickets]

                return Response({
                    'success': True,
                    'data': self.get_serializer(tickets_list, many=True).data,
                    'message': f"Successfully created {len(tickets_list)} ticket(s)",
                }, status=status.HTTP_201_CREATED)
            except ValidationError as e:
                return Response({
                    'success': False,
                    'error': str(e),
                    'message': 'Failed to create ticket',
                }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def validate_entry(self, request, pk=None):
        """Validate ticket at entry gate"""
        ticket = self.get_object()
        station_id = request.data.get('station_id')

        if not station_id:
            return Response(
                {'error': 'Station ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = ValidationService.validate_entry(
            ticket.ticket_number,
            station_id
        )
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def validate_exit(self, request, pk=None):
        """Validate ticket at exit gate"""
        ticket = self.get_object()
        station_id = request.data.get('station_id')

        if not station_id:
            return Response(
                {'error': 'Station ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = ValidationService.validate_exit(
            ticket.ticket_number,
            station_id
        )
        return Response(
            result,
            status=status.HTTP_200_OK if result['is_valid'] else status.HTTP_402_PAYMENT_REQUIRED
        )

    @action(detail=True, methods=['post'])
    def upgrade(self, request, pk=None):
        """Upgrade ticket for additional stations"""
        ticket = self.get_object()
        new_station_count = request.data.get('stations_count')
        payment_confirmed = request.data.get('payment_confirmed', False)

        if not new_station_count:
            return Response(
                {'error': 'Number of stations required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        success, result = self.ticket_service.upgrade_ticket(
            ticket.ticket_number,
            new_station_count,
            payment_confirmed
        )

        if success:
            # Reset upgrade flags if successful
            ticket.needs_upgrade = False

            # If we have a temp_exit_station, finalize the exit
            if ticket.temp_exit_station_id:
                ticket.exit_station_id = ticket.temp_exit_station_id
                ticket.temp_exit_station_id = None
                ticket.exit_time = timezone.now()
                ticket.status = 'USED'
                ticket.save(update_fields=[
                    'needs_upgrade', 'exit_station_id',
                    'temp_exit_station_id', 'exit_time', 'status'
                ])
            else:
                ticket.save(update_fields=['needs_upgrade'])

            return Response(result)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='validate-scan', permission_classes=[AllowAny])
    @transaction.atomic
    def validate_scan(self, request):
        """
        Unified endpoint to handle both entry and exit scans
        """
        ticket_number = request.data.get('ticket_number')
        station_id = request.data.get('station_id')

        # Validate input
        if not ticket_number or not station_id:
            return Response(
                {'error': 'Ticket number and station ID are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            # Get ticket with select_for_update to prevent race conditions
            ticket = Ticket.objects.select_for_update().get(ticket_number=ticket_number)

            # Check expiration first
            if ticket.valid_until < timezone.now() and ticket.status == 'ACTIVE':
                ticket.status = 'EXPIRED'
                ticket.save(update_fields=['status'])
                return Response({
                    'is_valid': False,
                    'message': 'Ticket has expired'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Determine scan type based on current ticket state
            if ticket.status == 'ACTIVE' and not ticket.entry_station_id:
                result = ValidationService.validate_entry(ticket_number, station_id)
                return Response({
                    **result,
                    'scan_type': 'ENTRY'
                }, status=status.HTTP_200_OK)

            elif ticket.status == 'IN_USE' and ticket.entry_station_id and not ticket.exit_station_id:
                result = ValidationService.validate_exit(ticket_number, station_id)
                status_code = self.get_status_code(result)
                return Response({
                    **result,
                    'scan_type': 'EXIT'
                }, status=status_code)

            else:
                return Response({
                    'is_valid': False,
                    'message': f'Ticket is in invalid state for scanning: {ticket.status}',
                    'current_status': ticket.status,
                    'has_entry': bool(ticket.entry_station_id),
                    'has_exit': bool(ticket.exit_station_id)
                }, status=status.HTTP_400_BAD_REQUEST)

        except Ticket.DoesNotExist:
            return Response({
                'is_valid': False,
                'message': 'Invalid ticket'
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'], url_path='pending-upgrades')
    def check_pending_upgrades(self, request):
        """
        Check for tickets that need upgrading for the current user
        """
        # Get tickets that need upgrading (marked with special status)
        pending_upgrades = Ticket.objects.filter(
            user=request.user,
            status='IN_USE',
            needs_upgrade=True
        ).select_related('entry_station', 'temp_exit_station').order_by('-updated_at')

        if not pending_upgrades.exists():
            return Response({
                "has_pending_upgrades": False,
                "message": "No pending ticket upgrades"
            })

        # Get the most recent ticket needing upgrade
        ticket = pending_upgrades.first()

        # Calculate upgrade details
        route_data = self.ticket_service.route_service.find_route(
            ticket.entry_station_id,
            ticket.temp_exit_station_id
        )

        if not route_data:
            return Response({
                "has_pending_upgrades": False,
                "message": "Invalid route data"
            })

        stations_count = route_data['num_stations']
        next_ticket_type, next_ticket_details = TicketChoices.get_next_ticket_type(stations_count)

        price_difference = next_ticket_details['price'] - ticket.price

        return Response({
            "has_pending_upgrades": True,
            "ticket": self.get_serializer(ticket).data,
            "upgrade_details": {
                "ticket_number": ticket.ticket_number,
                "stations_count": stations_count,
                "max_stations": ticket.max_stations,
                "new_ticket_type": next_ticket_type,
                "upgrade_price": price_difference,
                "entry_station": ticket.entry_station.name,
                "temp_exit_station": ticket.temp_exit_station.name,
            },
            "message": "Ticket requires upgrade to exit"
        })

    @staticmethod
    def get_status_code(result):
        if result['is_valid']:
            return status.HTTP_200_OK
        elif result.get('needs_upgrade'):
            return status.HTTP_402_PAYMENT_REQUIRED
        else:
            return status.HTTP_400_BAD_REQUEST

    def partial_update(self, request, *args, **kwargs):
        """Handle updates for entry/exit station IDs"""
        instance = self.get_object()

        # Basic validation for status transitions
        new_status = request.data.get('status')
        if new_status:
            if new_status == 'IN_USE' and instance.status != 'ACTIVE':
                return Response(
                    {'error': 'Can only change to IN_USE from ACTIVE status'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if new_status == 'USED' and instance.status != 'IN_USE':
                return Response(
                    {'error': 'Can only change to USED from IN_USE status'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Handle entry and exit times automatically
        if 'entry_station_id' in request.data and not instance.entry_time:
            request.data['entry_time'] = timezone.now()

        if 'exit_station_id' in request.data and not instance.exit_time:
            request.data['exit_time'] = timezone.now()

        return super().partial_update(request, *args, **kwargs)
