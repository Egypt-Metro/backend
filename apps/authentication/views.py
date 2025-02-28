# apps/authentication/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
import logging

from .serializers import (
    RequestPasswordResetSerializer,
    ValidateTokenSerializer,
    ResetPasswordSerializer
)
from .services import PasswordResetService

logger = logging.getLogger(__name__)
User = get_user_model()


class RequestPasswordResetView(APIView):
    serializer_class = RequestPasswordResetSerializer

    @extend_schema(
        summary="Request password reset",
        description="Send a password reset email to the user",
        responses={200: None}
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                user = User.objects.get(email=serializer.validated_data['email'])
                token = PasswordResetService.create_reset_token(user)

                if PasswordResetService.send_reset_email(user, token):
                    return Response(
                        {"message": "Password reset email sent successfully"},
                        status=status.HTTP_200_OK
                    )
                else:
                    return Response(
                        {"error": "Failed to send reset email"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            except Exception as e:
                logger.error(f"Password reset request error: {str(e)}")
                return Response(
                    {"error": "An error occurred processing your request"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ValidateTokenView(APIView):
    serializer_class = ValidateTokenSerializer

    @extend_schema(
        summary="Validate reset token",
        description="Check if a password reset token is valid",
        responses={200: None}
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            is_valid = PasswordResetService.validate_token(token)

            return Response({"is_valid": is_valid}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    serializer_class = ResetPasswordSerializer

    @extend_schema(
        summary="Reset password",
        description="Reset user's password using a valid token",
        responses={200: None}
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']

            if PasswordResetService.reset_password(token, new_password):
                return Response(
                    {"message": "Password reset successful"},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"error": "Invalid or expired token"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
