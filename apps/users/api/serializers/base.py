# apps/users/api/serializers/base.py
from rest_framework import serializers
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from typing import Dict, Any, Optional


class BaseUserSerializer(serializers.ModelSerializer):
    """
    Base serializer with common functionality for user-related serializers.

    Features:
    - Subscription details caching
    - Common validation methods
    - Error handling
    - Audit logging
    """

    class Meta:
        abstract = True

    def get_subscription_details(self, obj) -> Dict[str, Any]:
        """
        Get cached subscription details for a user.
        Uses caching to improve performance.
        """
        cache_key = f'subscription_details_{obj.id}'
        cached_details = cache.get(cache_key)

        if cached_details is not None:
            return cached_details

        details = {
            'type': obj.get_subscription_type_display(),
            'is_active': obj.is_active,
            'payment_method': obj.get_payment_method_display(),
            'expires_at': self._get_subscription_expiry(obj),
            'features': self._get_subscription_features(obj),
            'status': self._get_subscription_status(obj)
        }

        # Cache for 5 minutes
        cache.set(cache_key, details, timeout=300)
        return details

    def _get_subscription_expiry(self, obj) -> Optional[str]:
        """Get subscription expiration date"""
        try:
            subscription = obj.subscription_set.latest('created_at')
            return subscription.expires_at
        except Exception:
            return None

    def _get_subscription_features(self, obj) -> Dict[str, bool]:
        """Get features available for user's subscription type"""
        return {
            'can_book_advance': obj.subscription_type != 'FREE',
            'priority_booking': obj.subscription_type == 'PREMIUM',
            'discounted_rates': obj.subscription_type in ['BASIC', 'PREMIUM'],
            'customer_support': True
        }

    def _get_subscription_status(self, obj) -> str:
        """Get current subscription status"""
        if not obj.is_active:
            return _('Inactive')
        if obj.subscription_type == 'FREE':
            return _('Free Tier')
        return _('Active')

    def validate_phone_number(self, value: str) -> str:
        """Validate phone number format"""
        if value and not value.startswith('01'):
            raise serializers.ValidationError(
                _('Phone number must start with 01')
            )
        return value

    def validate_email(self, value: str) -> str:
        """Validate and normalize email"""
        return value.lower().strip()

    def to_representation(self, instance) -> Dict[str, Any]:
        """Enhanced representation with additional data"""
        data = super().to_representation(instance)
        request = self.context.get('request')

        if request and request.user.is_staff:
            data['admin_data'] = self._get_admin_data(instance)

        return data

    def _get_admin_data(self, obj) -> Dict[str, Any]:
        """Get additional data for admin users"""
        return {
            'created_at': obj.created_at,
            'updated_at': obj.updated_at,
            'last_login': obj.last_login,
            'is_active': obj.is_active,
            'is_staff': obj.is_staff
        }
