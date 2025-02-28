# apps/users/api/views/profile.py
from rest_framework.permissions import IsAuthenticated
from django.core.cache import cache

from apps.users.constants.choices import UserMessages
from .base import BaseAPIView
from ..serializers.profile import ProfileSerializer
from ..serializers.user import UpdateUserSerializer
from ...services.profile_service import ProfileService
from ...utils.response_helpers import ApiResponse
from ...utils.decorators import log_api_request


class UserProfileView(BaseAPIView):
    """Handle user profile operations with caching"""
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    @log_api_request
    def get(self, request):
        try:
            # Try to get profile from cache
            cache_key = f'profile_{request.user.id}'
            profile = cache.get(cache_key)

            if not profile:
                profile = request.user
                # Cache profile for 5 minutes
                cache.set(cache_key, profile, timeout=300)

            serializer = self.serializer_class(profile)
            return ApiResponse.success(data=serializer.data)
        except Exception as e:
            return ApiResponse.error(str(e))


class UpdateUserView(BaseAPIView):
    """Handle user profile updates with validation"""
    permission_classes = [IsAuthenticated]
    serializer_class = UpdateUserSerializer

    @log_api_request
    def patch(self, request):
        serializer = self.serializer_class(
            request.user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            try:
                updated_user = ProfileService.update_profile(
                    request.user,
                    serializer.validated_data
                )

                # Invalidate cache
                cache.delete(f'profile_{request.user.id}')

                response_serializer = ProfileSerializer(updated_user)
                return ApiResponse.success(
                    message=UserMessages.PROFILE_UPDATED,
                    data=response_serializer.data
                )
            except Exception as e:
                return ApiResponse.error(str(e))
        return ApiResponse.validation_error(serializer.errors)
