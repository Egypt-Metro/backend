# apps/users/api/serializers/user.py
from rest_framework import serializers

from apps.users.constants.choices import SubscriptionType
from ...models import User
from ...utils.validators import validate_phone_number, validate_subscription_type
from .base import BaseUserSerializer


class UserSerializer(BaseUserSerializer):
    """Enhanced user serializer with detailed information"""
    full_name = serializers.SerializerMethodField()
    subscription_status = serializers.SerializerMethodField()
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'phone_number', 'national_id',
            'subscription_type', 'payment_method', 'payment_method_display',
            'balance', 'subscription_status', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['password', 'balance', 'created_at', 'updated_at']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username

    def get_subscription_status(self, obj):
        return self.get_subscription_details(obj)


class UpdateUserSerializer(BaseUserSerializer):
    """Enhanced update serializer with validation"""
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number',
            'subscription_type', 'payment_method'
        ]
        read_only_fields = ['balance']

    def validate_phone_number(self, value):
        if value:
            return validate_phone_number(value)
        return value

    def validate_subscription_type(self, value):
        if value:
            return validate_subscription_type(value)
        return value

    def validate(self, data):
        """Additional validation for update operations"""
        if 'subscription_type' in data and 'payment_method' not in data:
            if data['subscription_type'] != SubscriptionType.FREE:
                raise serializers.ValidationError({
                    'payment_method': 'Payment method is required for paid subscriptions'
                })
        return data
