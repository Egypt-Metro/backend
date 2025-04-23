from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
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


class TicketViewSet(viewsets.ModelViewSet):
    serializer_class = TicketSerializer
    permission_classes = [IsAuthenticated]
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
            return Response(result)
        return Response(result, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='validate-scan')
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

    @staticmethod
    def get_status_code(result):
        if result['is_valid']:
            return status.HTTP_200_OK
        elif result.get('upgrade_required'):
            return status.HTTP_402_PAYMENT_REQUIRED
        else:
            return status.HTTP_400_BAD_REQUEST
