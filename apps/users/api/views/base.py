# apps/users/api/views/base.py
from rest_framework.views import APIView
from ...utils.response_helpers import ApiResponse
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.decorators import api_view


class BaseAPIView(APIView):
    """Base API view with common functionality"""

    def handle_exception(self, exc):
        """Global exception handler for API views"""
        return ApiResponse.error(str(exc))


@api_view(["GET"])
def get_superusers(request):
    User = get_user_model()
    superusers = User.objects.filter(is_superuser=True).values("email")
    return Response({"superusers": list(superusers)})
