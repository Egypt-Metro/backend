import logging
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    UpdateUserSerializer,
)

logger = logging.getLogger(__name__)


# 1. Register View
class RegisterView(APIView):
    """
    Handles user registration. Creates a new user and returns JWT tokens.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        logger.info(f"Registration attempt for email: {request.data.get('email')}")
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            logger.info(f"User registered successfully: {user.email}")
            refresh = RefreshToken.for_user(user)
            return Response(
                {
                    "message": "User registered successfully",
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                status=status.HTTP_201_CREATED,
            )

        logger.warning(f"Registration failed: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 2. Login View
class LoginView(APIView):
    """
    Handles user login. Authenticates credentials and returns JWT tokens.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        logger.info(f"Login attempt for username: {request.data.get('username')}")
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                username=serializer.validated_data["username"],
                password=serializer.validated_data["password"],
            )
            if user:
                logger.info(f"User logged in successfully: {user.username}")
                refresh = RefreshToken.for_user(user)
                return Response(
                    {
                        "message": "Login successful",
                        "refresh": str(refresh),
                        "access": str(refresh.access_token),
                    },
                    status=status.HTTP_200_OK,
                )

            logger.warning(
                f"Invalid credentials for username: {request.data.get('username')}"
            )
            return Response(
                {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
            )

        logger.error(f"Validation error during login: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 3. User Profile View
class UserProfileView(APIView):
    """
    Retrieves the profile of the authenticated user.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        logger.info(f"Profile retrieved for user: {user.email}")
        return Response(serializer.data, status=status.HTTP_200_OK)


# 4. Update User View
class UpdateUserView(APIView):
    """
    Updates the profile of the authenticated user.
    """

    permission_classes = [IsAuthenticated]

    def patch(self, request):
        user = request.user
        serializer = UpdateUserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            updated_user = serializer.save()
            logger.info(f"Profile updated successfully for user: {updated_user.email}")
            return Response(serializer.data, status=status.HTTP_200_OK)

        logger.warning(
            f"Failed to update profile for user: {user.email} - {serializer.errors}"
        )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
