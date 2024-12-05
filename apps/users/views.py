from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated  # Import permissions
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import User
from .serializers import RegisterSerializer, LoginSerializer, UserSerializer, UpdateUserSerializer


# 1. Register View (public, no authentication required)
class RegisterView(APIView):
    permission_classes = [AllowAny]  # Allow any user to register (no authentication required)

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()  # Save the user (call create method in serializer)
            # Generate JWT token for the registered user
            refresh = RefreshToken.for_user(user)
            return Response({
                'message': 'User registered successfully',
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 2. Login View (public, no authentication required for login request)
class LoginView(APIView):
    permission_classes = [AllowAny]  # Allow any user to log in (no authentication required)

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            # Authenticate the user using the email and password
            user = authenticate(
                request, email=serializer.validated_data['email'], password=serializer.validated_data['password']
            )
            if user:
                # Generate JWT token for authenticated user
                refresh = RefreshToken.for_user(user)
                return Response({
                    'message': 'Login successful',
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }, status=status.HTTP_200_OK)
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# 3. User Profile View (requires authentication)
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated to view the profile

    def get(self, request):
        user = request.user  # Assuming the user is authenticated with a valid JWT token
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


# 4. Update User View (requires authentication)
class UpdateUserView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated to update profile

    def patch(self, request):
        user = request.user  # Get the authenticated user
        serializer = UpdateUserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()  # Save the updated user data
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
