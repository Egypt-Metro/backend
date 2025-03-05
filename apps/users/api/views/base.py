# apps/users/api/views/base.py
from time import timezone
from typing import Any
import logging
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils.translation import gettext_lazy as _
from ...utils.response_helpers import ApiResponse
from ...utils.decorators import log_api_request, rate_limit

logger = logging.getLogger(__name__)


class BaseAPIView(APIView):
    """
    Base API view with enhanced functionality.

    Features:
    - Comprehensive exception handling
    - Request logging
    - Response formatting
    - Cache management
    - Rate limiting
    """

    def handle_exception(self, exc: Exception) -> Response:
        """Enhanced exception handler with logging"""
        logger.error(
            f"API Error: {str(exc)}",
            exc_info=True,
            extra={
                'view': self.__class__.__name__,
                'user_id': getattr(self.request.user, 'id', None)
            }
        )

        if hasattr(exc, 'detail'):
            detail = exc.detail
        else:
            detail = str(exc)

        return ApiResponse.error(
            message=detail,
            status_code=self._get_exception_status_code(exc)
        )

    def _get_exception_status_code(self, exc: Exception) -> int:
        """Determine appropriate status code for exception"""
        if hasattr(exc, 'status_code'):
            return exc.status_code
        return status.HTTP_500_INTERNAL_SERVER_ERROR

    def finalize_response(self, request: Any, response: Response, *args: Any, **kwargs: Any) -> Response:
        """Enhanced response finalization"""
        if not hasattr(response, 'data'):
            return response

        # Add request ID for tracking
        response.data['request_id'] = request.META.get('REQUEST_ID')

        # Add API version
        response.data['api_version'] = '1.0'

        return super().finalize_response(request, response, *args, **kwargs)

    def get_cache_key(self, prefix: str, identifier: str) -> str:
        """Generate standardized cache key"""
        return f"{prefix}_{identifier}"

    def clear_user_cache(self, user_id: int) -> None:
        """Clear all user-related cache"""
        cache_keys = [
            f'profile_{user_id}',
            f'subscription_{user_id}',
            f'preferences_{user_id}'
        ]
        cache.delete_many(cache_keys)


@api_view(["GET"])
@permission_classes([IsAdminUser])
@log_api_request
@rate_limit(requests=10, duration=60)
def get_superusers(request) -> Response:
    """
    Get list of superusers with caching.

    Permissions: Admin only
    Cache: 5 minutes
    Rate limit: 10 requests per minute
    """
    cache_key = 'superusers_list'
    cached_data = cache.get(cache_key)

    if cached_data is not None:
        return Response(cached_data)

    try:
        User = get_user_model()
        superusers = User.objects.filter(is_superuser=True).values(
            "id", "email", "last_login", "date_joined"
        )

        data = {
            "superusers": list(superusers),
            "count": len(superusers),
            "generated_at": timezone.now()
        }

        # Cache for 5 minutes
        cache.set(cache_key, data, timeout=300)

        return Response(data)

    except Exception as e:
        logger.error(f"Error fetching superusers: {str(e)}", exc_info=True)
        return Response(
            {"error": _("Failed to fetch superusers")},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
