from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ...services.wallet_service import WalletService
from ...models.transaction import Transaction
from ..serializers.transaction_serializers import (
    TransactionListSerializer,
    TransactionDetailSerializer,
    TransactionFilterSerializer
)


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for transaction operations"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return TransactionDetailSerializer
        return TransactionListSerializer

    @action(detail=False, methods=['get'])
    def filter(self, request):
        """Filter transactions"""
        serializer = TransactionFilterSerializer(data=request.query_params)

        if serializer.is_valid():
            transactions = WalletService.get_transaction_history(
                user=request.user,
                transaction_type=serializer.validated_data.get('type'),
                status=serializer.validated_data.get('status'),
                start_date=serializer.validated_data.get('start_date'),
                end_date=serializer.validated_data.get('end_date'),
                limit=serializer.validated_data.get('limit')
            )

            list_serializer = TransactionListSerializer(transactions, many=True)

            return Response({
                'success': True,
                'count': len(transactions),
                'data': list_serializer.data
            })

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent transactions"""
        transactions = WalletService.get_transaction_history(
            user=request.user,
            limit=5
        )

        serializer = TransactionListSerializer(transactions, many=True)

        return Response({
            'success': True,
            'count': len(transactions),
            'data': serializer.data
        })
