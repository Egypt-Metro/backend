# apps/users/utils/validators.py
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from ..constants.choices import SubscriptionType

# Username validator
username_validator = RegexValidator(
    regex=r'^[a-zA-Z0-9_]+$',
    message='Username must contain only letters, numbers, and underscores'
)


def validate_username(value):
    """Validate username format"""
    if len(value) < 3:
        raise ValidationError('Username must be at least 3 characters long')
    if len(value) > 30:
        raise ValidationError('Username must be at most 30 characters long')
    try:
        username_validator(value)
    except ValidationError:
        raise ValidationError('Username must contain only letters, numbers, and underscores')
    return value


def validate_phone_number(value):
    """Validate Egyptian phone number format"""
    if not value:
        return value
    if not value.startswith('01') or len(value) != 11:
        raise ValidationError('Phone number must start with 01 and be 11 digits long')
    if not value.isdigit():
        raise ValidationError('Phone number must contain only digits')
    return value


def validate_national_id(value):
    """Validate Egyptian national ID format"""
    if not value:
        return value
    if not value.isdigit() or len(value) != 14:
        raise ValidationError('National ID must be 14 digits')
    # Add additional validation logic for national ID if needed
    return value


def validate_subscription_type(value):
    """Validate subscription type"""
    if value not in [choice[0] for choice in SubscriptionType.choices]:
        raise ValidationError('Invalid subscription type')
    return value
