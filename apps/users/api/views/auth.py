# apps/users/api/views/auth.py
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.core.cache import cache
from .base import BaseAPIView
from ..serializers.auth import RegisterSerializer, LoginSerializer
from ...services.auth_service import AuthService
from ...utils.response_helpers import ApiResponse
from ...constants.messages import UserMessages
from ...utils.decorators import log_api_request


class RegisterView(BaseAPIView):
    """Handle user registration with enhanced security and validation"""
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    @log_api_request
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                tokens = AuthService.generate_tokens(user)

                # Cache user data
                cache.set(f'user_{user.id}', user, timeout=300)

                return ApiResponse.success(
                    message=UserMessages.REGISTRATION_SUCCESS,
                    data={
                        'user': {
                            'id': user.id,
                            'email': user.email,
                            'username': user.username,
                            'full_name': user.get_full_name()
                        },
                        **tokens
                    },
                    status_code=status.HTTP_201_CREATED
                )
            except Exception as e:
                return ApiResponse.error(
                    message=str(e),
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        return ApiResponse.validation_error(serializer.errors)


class LoginView(BaseAPIView):
    """Handle user login with rate limiting and security features"""
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    @log_api_request
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return ApiResponse.validation_error(serializer.errors)

        try:
            auth_service = AuthService()
            user = auth_service.authenticate_user(
                request.data.get('username'),
                request.data.get('password')
            )

            if not user:
                return ApiResponse.error(
                    message=UserMessages.INVALID_CREDENTIALS,
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            tokens = auth_service.generate_tokens(user)
            return ApiResponse.success(
                message=UserMessages.LOGIN_SUCCESS,
                data={
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'username': user.username,
                        'full_name': user.get_full_name()
                    },
                    **tokens
                }
            )
        except Exception as e:
            return ApiResponse.error(str(e))
