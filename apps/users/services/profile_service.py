# apps/users/services/profile_service.py

import logging
from django.db import transaction
from django.core.cache import cache
from apps.users.constants.messages import UserMessages

logger = logging.getLogger(__name__)


class ProfileService:
    """Service for handling profile-related operations"""

    @staticmethod
    @transaction.atomic
    def update_profile(user, validated_data):
        """
        Update user profile with comprehensive error handling and logging
        """
        try:
            # Track changes for logging
            changes = {}

            # Handle email update
            if 'email' in validated_data:
                old_email = user.email
                user.email = validated_data['email']
                changes['email'] = {'old': old_email, 'new': user.email}

            # Handle username update
            if 'username' in validated_data:
                old_username = user.username
                user.username = validated_data['username']
                changes['username'] = {'old': old_username, 'new': user.username}

            # Handle phone number update
            if 'phone_number' in validated_data:
                old_phone = user.phone_number
                user.phone_number = validated_data['phone_number']
                changes['phone_number'] = {'old': old_phone, 'new': user.phone_number}

            # Handle national ID update
            if 'national_id' in validated_data:
                old_national_id = user.national_id
                user.national_id = validated_data['national_id']
                changes['national_id'] = {'old': old_national_id, 'new': user.national_id}

            # Update other fields
            for field in ['first_name', 'last_name', 'subscription_type', 'payment_method']:
                if field in validated_data:
                    old_value = getattr(user, field)
                    setattr(user, field, validated_data[field])
                    changes[field] = {'old': old_value, 'new': validated_data[field]}

            # Save changes
            user.save()

            # Clear cache
            cache_keys = [
                f'profile_{user.id}',
                f'user_details_{user.id}',
                f'user_subscription_{user.id}'
            ]
            cache.delete_many(cache_keys)

            # Log changes
            logger.info(
                f"Profile updated for user {user.id}",
                extra={
                    'user_id': user.id,
                    'changes': changes
                }
            )

            return user

        except Exception as e:
            logger.error(
                f"Profile update failed for user {user.id}",
                extra={
                    'user_id': user.id,
                    'error': str(e),
                    'data': validated_data
                }
            )
            raise ValueError(UserMessages.PROFILE_UPDATE_FAILED)
