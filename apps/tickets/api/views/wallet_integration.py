from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.wallet.services.integration_service import (
    TicketIntegrationService,
    SubscriptionIntegrationService
)


class WalletTicketMixin:
    """Mixin to add wallet payment functionality to ticket views"""

    @action(detail=False, methods=['post'], url_path='purchase-with-wallet')
    def purchase_with_wallet(self, request):
        """Purchase a ticket using wallet balance"""
        ticket_type = request.data.get('ticket_type')
        quantity = int(request.data.get('quantity', 1))

        if not ticket_type:
            return Response({
                'success': False,
                'message': 'Ticket type is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if quantity < 1:
            return Response({
                'success': False,
                'message': 'Quantity must be at least 1'
            }, status=status.HTTP_400_BAD_REQUEST)

        result = TicketIntegrationService.purchase_ticket(
            user=request.user,
            ticket_type=ticket_type,
            quantity=quantity
        )

        if result['success']:
            # Use your existing ticket serializer to format the response
            tickets = result['tickets']
            if isinstance(tickets, list):
                ticket_data = self.get_serializer(tickets, many=True).data
            else:
                ticket_data = self.get_serializer(tickets).data

            return Response({
                'success': True,
                'message': result['message'],
                'wallet_balance': result['new_balance'],
                'tickets': ticket_data
            })
        else:
            return Response({
                'success': False,
                'message': result['message'],
                'requires_top_up': result.get('requires_top_up', False),
                'amount_required': result.get('amount_required', None)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], url_path='upgrade-with-wallet')
    def upgrade_with_wallet(self, request, pk=None):
        """Upgrade a ticket using wallet balance"""
        ticket = self.get_object()
        new_ticket_type = request.data.get('new_ticket_type')

        if not new_ticket_type:
            return Response({
                'success': False,
                'message': 'New ticket type is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        result = TicketIntegrationService.upgrade_ticket(
            user=request.user,
            ticket_number=ticket.ticket_number,
            new_ticket_type=new_ticket_type
        )

        if result['success']:
            # Use your existing ticket serializer to format the response
            from apps.tickets.models.ticket import Ticket
            updated_ticket = Ticket.objects.get(pk=ticket.pk)

            return Response({
                'success': True,
                'message': result['message'],
                'wallet_balance': result['new_balance'],
                'ticket': self.get_serializer(updated_ticket).data
            })
        else:
            return Response({
                'success': False,
                'message': result['message'],
                'requires_top_up': result.get('requires_top_up', False),
                'amount_required': result.get('amount_required', None)
            }, status=status.HTTP_400_BAD_REQUEST)


class WalletSubscriptionMixin:
    """Mixin to add wallet payment functionality to subscription views"""

    @action(detail=False, methods=['post'], url_path='purchase-with-wallet')
    def purchase_with_wallet(self, request):
        """Purchase a subscription using wallet balance"""
        subscription_type = request.data.get('subscription_type')
        zones_count = int(request.data.get('zones_count', 0))
        start_station_id = request.data.get('start_station_id')
        end_station_id = request.data.get('end_station_id')

        if not subscription_type or zones_count < 1:
            return Response({
                'success': False,
                'message': 'Subscription type and zones count are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        result = SubscriptionIntegrationService.purchase_subscription(
            user=request.user,
            subscription_type=subscription_type,
            zones_count=zones_count,
            start_station_id=start_station_id,
            end_station_id=end_station_id
        )

        if result['success']:
            # Use your existing subscription serializer
            from ..serializers.subscription_serializers import SubscriptionDetailSerializer
            subscription_data = SubscriptionDetailSerializer(result['subscription']).data

            return Response({
                'success': True,
                'message': result['message'],
                'wallet_balance': result['new_balance'],
                'subscription': subscription_data
            })
        else:
            return Response({
                'success': False,
                'message': result['message'],
                'requires_top_up': result.get('requires_top_up', False),
                'amount_required': result.get('amount_required', None)
            }, status=status.HTTP_400_BAD_REQUEST)
