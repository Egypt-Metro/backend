from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from django.db import transaction

from ...services.wallet_service import WalletService
from ...models.wallet import UserWallet
from ...models.payment_method import PaymentMethod
from ..serializers.wallet_serializers import (
    WalletSerializer,
    WalletAddFundsSerializer,
    WalletWithdrawFundsSerializer
)
from ..serializers.transaction_serializers import TransactionListSerializer


class WalletViewSet(viewsets.GenericViewSet):
    """ViewSet for wallet operations"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserWallet.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def my_wallet(self, request):
        """Get user's wallet details"""
        wallet = WalletService.get_or_create_wallet(request.user)
        serializer = WalletSerializer(wallet)

        return Response({
            'success': True,
            'data': serializer.data
        })

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def add_funds(self, request):
        """Add funds to user's wallet"""
        serializer = WalletAddFundsSerializer(data=request.data)

        if serializer.is_valid():
            payment_method = None
            if serializer.validated_data.get('payment_method_id'):
                try:
                    payment_method = PaymentMethod.objects.get(
                        id=serializer.validated_data['payment_method_id'],
                        user=request.user,
                        is_active=True
                    )
                except PaymentMethod.DoesNotExist:
                    return Response({
                        'success': False,
                        'message': 'Payment method not found'
                    }, status=status.HTTP_404_NOT_FOUND)

            try:
                result = WalletService.add_funds(
                    user=request.user,
                    amount=serializer.validated_data['amount'],
                    payment_method=payment_method,
                    description=serializer.validated_data.get('description')
                )

                response_data = {
                    'success': result['success'],
                    'message': result['message'],
                    'balance': result['wallet'].balance
                }

                if result['success']:
                    response_data['transaction'] = TransactionListSerializer(result['transaction']).data

                return Response(response_data)

            except ValidationError as e:
                return Response({
                    'success': False,
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def withdraw_funds(self, request):
        """Withdraw funds from user's wallet"""
        serializer = WalletWithdrawFundsSerializer(data=request.data)

        if serializer.is_valid():
            try:
                result = WalletService.withdraw_funds(
                    user=request.user,
                    amount=serializer.validated_data['amount'],
                    description=serializer.validated_data.get('description')
                )

                response_data = {
                    'success': result['success'],
                    'message': result['message'],
                    'balance': result['wallet'].balance
                }

                if result['success']:
                    response_data['transaction'] = TransactionListSerializer(result['transaction']).data

                return Response(response_data)

            except ValidationError as e:
                return Response({
                    'success': False,
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
