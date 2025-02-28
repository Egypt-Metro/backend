# apps/users/services/data_integrity_service.py
import logging
from django.db import transaction

from apps.users.constants.choices import SubscriptionType
from ..models import User

logger = logging.getLogger(__name__)


class UserDataIntegrityService:
    """Service to handle data integrity and migrations"""

    @staticmethod
    @transaction.atomic
    def validate_existing_users():
        """
        Validate and fix data for existing users.
        Returns tuple of (success_count, error_count, error_details)
        """
        success_count = 0
        error_count = 0
        error_details = []

        for user in User.objects.all():
            try:
                # Validate required fields
                if not user.email:
                    user.email = f"user_{user.id}@example.com"
                    logger.warning(f"Generated email for user {user.id}")

                # Ensure national_id exists
                if not user.national_id:
                    user.national_id = f"TEMP{user.id:010d}"
                    logger.warning(f"Generated temporary national_id for user {user.id}")

                # Validate phone number
                if user.phone_number and not user.phone_number.startswith('01'):
                    user.phone_number = f"01{user.phone_number[-9:]}"
                    logger.warning(f"Fixed phone number format for user {user.id}")

                user.save()
                success_count += 1

            except Exception as e:
                error_count += 1
                error_details.append({
                    'user_id': user.id,
                    'error': str(e)
                })
                logger.error(f"Error processing user {user.id}: {str(e)}")

        return success_count, error_count, error_details

    @staticmethod
    def generate_report():
        """Generate report of user data status"""
        return {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(is_active=True).count(),
            'with_phone': User.objects.exclude(phone_number__isnull=True).count(),
            'with_national_id': User.objects.exclude(national_id__isnull=True).count(),
            'subscribed_users': User.objects.filter(
                subscription_type__in=[
                    SubscriptionType.BASIC,
                    SubscriptionType.PREMIUM
                ]
            ).count(),
            'free_users': User.objects.filter(
                subscription_type=SubscriptionType.FREE
            ).count(),
            'missing_subscription': User.objects.filter(
                subscription_type__isnull=True
            ).count(),
        }
