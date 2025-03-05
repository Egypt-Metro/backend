# apps/users/api/serializers/user.py
import logging
from rest_framework import serializers
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from ...models import User
from .base import BaseUserSerializer
from apps.users.constants.messages import UserMessages
from apps.users.utils.validators import (
    validate_phone_number,
    validate_national_id,
    validate_username,
    username_validator
)

logger = logging.getLogger(__name__)


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


class UpdateUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=False, validators=[EmailValidator()])
    username = serializers.CharField(
        required=False,
        validators=[username_validator, validate_username]
    )
    phone_number = serializers.CharField(required=False)
    national_id = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = [
            'email', 'username', 'first_name', 'last_name',
            'phone_number', 'national_id', 'subscription_type',
            'payment_method'
        ]
        read_only_fields = ['balance', 'created_at', 'updated_at']

    def validate(self, data):
        user = self.context['request'].user

        try:
            # Email validation
            if 'email' in data:
                email = data['email'].lower()
                if User.objects.exclude(id=user.id).filter(email=email).exists():
                    raise serializers.ValidationError({
                        'email': UserMessages.EMAIL_EXISTS
                    })
                data['email'] = email

            # Username validation
            if 'username' in data:
                username = data['username'].lower()
                if User.objects.exclude(id=user.id).filter(username=username).exists():
                    raise serializers.ValidationError({
                        'username': UserMessages.USERNAME_EXISTS
                    })
                data['username'] = username

            # Phone number validation
            if 'phone_number' in data:
                try:
                    data['phone_number'] = validate_phone_number(data['phone_number'])
                except ValidationError as e:
                    raise serializers.ValidationError({
                        'phone_number': str(e)
                    })

            # National ID validation
            if 'national_id' in data:
                try:
                    data['national_id'] = validate_national_id(data['national_id'])
                except ValidationError as e:
                    raise serializers.ValidationError({
                        'national_id': str(e)
                    })

            return data

        except Exception as e:
            logger.error(f"Validation error: {str(e)}")
            raise serializers.ValidationError(str(e))
