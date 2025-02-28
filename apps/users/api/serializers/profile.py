# apps/users/api/serializers/profile.py
from rest_framework import serializers
from ...models import User
from .base import BaseUserSerializer


class ProfileSerializer(BaseUserSerializer):
    """Enhanced profile serializer with detailed information"""
    full_name = serializers.SerializerMethodField()
    subscription_details = serializers.SerializerMethodField()
    payment_method_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    subscription_type_display = serializers.CharField(source='get_subscription_type_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'phone_number', 'national_id',
            'subscription_type', 'subscription_type_display',
            'payment_method', 'payment_method_display',
            'balance', 'subscription_details',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['email', 'username', 'balance', 'created_at', 'updated_at']

    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username
