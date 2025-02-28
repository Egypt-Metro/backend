# apps/users/utils/validators.py
from django.core.exceptions import ValidationError
from ..constants.choices import SubscriptionType


def validate_phone_number(value):
    if not value.startswith('01') or len(value) != 11:
        raise ValidationError('Phone number must start with 01 and be 11 digits long')
    return value


def validate_national_id(value):
    if not value.isdigit() or len(value) != 14:
        raise ValidationError('National ID must be 14 digits')
    return value


def validate_subscription_type(value):
    if value not in [choice[0] for choice in SubscriptionType.choices]:
        raise ValidationError('Invalid subscription type')
    return value
