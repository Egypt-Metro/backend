# apps/users/api/serializers/base.py
from rest_framework import serializers


class BaseUserSerializer(serializers.ModelSerializer):
    """Base serializer with common user fields and methods"""

    def get_subscription_details(self, obj):
        return {
            'type': obj.get_subscription_type_display(),
            'is_active': obj.is_active,
            'payment_method': obj.get_payment_method_display(),
            'status': 'Active' if obj.is_active else 'Inactive'
        }
