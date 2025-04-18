from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.db import transaction

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
        return Ticket.objects.filter(user=self.request.user)

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
