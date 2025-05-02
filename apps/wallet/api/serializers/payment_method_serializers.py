from rest_framework import serializers
from ...models.payment_method import PaymentMethod


class PaymentMethodListSerializer(serializers.ModelSerializer):
    """Serializer for listing payment methods"""

    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'payment_type', 'card_last4', 'card_brand',
            'is_default', 'is_active', 'name'
        ]


class PaymentMethodDetailSerializer(serializers.ModelSerializer):
    """Serializer for payment method details"""

    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'payment_type', 'card_last4', 'card_brand',
            'card_expiry_month', 'card_expiry_year',
            'is_default', 'is_active', 'name',
            'created_at', 'updated_at'
        ]


class PaymentMethodCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating payment methods"""

    class Meta:
        model = PaymentMethod
        fields = [
            'payment_type', 'card_last4', 'card_brand',
            'card_expiry_month', 'card_expiry_year',
            'is_default', 'name'
        ]

    def create(self, validated_data):
        # Set user from context
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)
