# apps/users/api/views/profile.py
import logging
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.core.cache import cache
from rest_framework import status
from apps.users.constants.messages import UserMessages
from .base import BaseAPIView
from ..serializers.profile import ProfileSerializer
from ..serializers.user import UpdateUserSerializer
from ...services.profile_service import ProfileService
from ...utils.response_helpers import ApiResponse
from ...utils.decorators import log_api_request, rate_limit

logger = logging.getLogger(__name__)


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
    permission_classes = [IsAuthenticated]
    serializer_class = UpdateUserSerializer

    @log_api_request
    @rate_limit(requests=5, duration=300)
    def patch(self, request):
        """Handle profile updates with validation"""
        try:
            serializer = self.serializer_class(
                request.user,
                data=request.data,
                partial=True,
                context={'request': request}
            )

            if not serializer.is_valid():
                return ApiResponse.validation_error(
                    serializer.errors,
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            updated_user = ProfileService.update_profile(
                request.user,
                serializer.validated_data
            )

            # Clear cache
            cache.delete_many([
                f'profile_{request.user.id}',
                f'user_details_{request.user.id}'
            ])

            response_serializer = ProfileSerializer(updated_user)
            return ApiResponse.success(
                message=UserMessages.PROFILE_UPDATED,
                data=response_serializer.data,
                status_code=status.HTTP_200_OK
            )

        except ValidationError as e:
            return ApiResponse.error(
                str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Profile update error: {str(e)}")
            return ApiResponse.error(
                UserMessages.SOMETHING_WENT_WRONG,
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
