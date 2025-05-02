from rest_framework import serializers
from ...models.wallet import UserWallet
from decimal import Decimal


class WalletSerializer(serializers.ModelSerializer):
    """Serializer for wallet data"""

    class Meta:
        model = UserWallet
        fields = ['id', 'balance', 'is_active', 'created_at', 'updated_at']
        read_only_fields = fields


class WalletAddFundsSerializer(serializers.Serializer):
    """Serializer for adding funds to wallet"""
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01')
    )
    payment_method_id = serializers.UUIDField(required=False)
    description = serializers.CharField(max_length=255, required=False)


class WalletWithdrawFundsSerializer(serializers.Serializer):
    """Serializer for withdrawing funds from wallet"""
    amount = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01')
    )
    description = serializers.CharField(max_length=255, required=False)
