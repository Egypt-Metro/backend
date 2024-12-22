# apps/users/serializers.py

from rest_framework import serializers
from .models import User


# 1. Registration Serializer
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "email",
            "username",
            "password",
            "confirm_password",
            "first_name",
            "last_name",
            "national_id",
            "phone_number",
        ]

    def validate(self, data):
        # Password match validation
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})

        # Unique email check
        if User.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError(
                {"email": "This email is already registered."}
            )

        # Unique username check
        if User.objects.filter(username=data["username"]).exists():
            raise serializers.ValidationError(
                {"username": "This username is already taken."}
            )

        # Phone number format validation
        if data.get("phone_number") and len(data["phone_number"]) != 11:
            raise serializers.ValidationError(
                {"phone_number": "Phone number must be 11 digits."}
            )
        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password", None)
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
            national_id=validated_data["national_id"],
            phone_number=validated_data.get("phone_number", None),
        )


# 2. Login Serializer
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, data):
        # Check if the user exists with the provided username
        if not User.objects.filter(username=data["username"]).exists():
            raise serializers.ValidationError(
                {"username": "User with this username does not exist."}
            )
        return data


# 3. User Serializer
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone_number",
            "national_id",
            "subscription_type",
            "payment_method",
            "balance",
            "created_at",
            "updated_at",
        ]
        # Ensure sensitive fields (like password) are not exposed
        read_only_fields = [
            "password"
        ]  # Password should not be returned in the response


# 4. Update User Serializer
class UpdateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "phone_number",
            "subscription_type",
            "payment_method",
        ]
        read_only_fields = ["balance"]  # Prevent direct updates to the balance field

        # Add validation for certain fields (optional)
        def validate_phone_number(self, value):
            if len(value) != 11:  # Example: Check if phone number is valid
                raise serializers.ValidationError("Phone number must be 11 digits.")
            return value
