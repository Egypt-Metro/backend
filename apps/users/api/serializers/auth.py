# apps/users/api/serializers/auth.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from ...utils.validators import validate_phone_number, validate_national_id
from ...constants.messages import UserMessages

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Enhanced registration serializer with comprehensive validation"""
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = [
            'email', 'username', 'password', 'confirm_password',
            'first_name', 'last_name', 'national_id', 'phone_number'
        ]

    def validate(self, data):
        if data.get('password') != data.get('confirm_password'):
            raise serializers.ValidationError({
                'password': UserMessages.PASSWORDS_NOT_MATCH
            })

        # Email uniqueness check
        email = data.get('email').lower()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({
                'email': UserMessages.EMAIL_EXISTS
            })

        # Username uniqueness check
        if User.objects.filter(username=data.get('username')).exists():
            raise serializers.ValidationError({
                'username': UserMessages.USERNAME_EXISTS
            })

        # Validate national ID and phone number
        if data.get('national_id'):
            validate_national_id(data['national_id'])
        if data.get('phone_number'):
            validate_phone_number(data['phone_number'])

        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        validated_data['email'] = validated_data['email'].lower()
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """Enhanced login serializer with better error handling"""
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        if not User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({
                'username': UserMessages.USER_NOT_FOUND
            })
        return data
