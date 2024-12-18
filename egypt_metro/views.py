import logging
from django.http import JsonResponse
from django.db import connection

logger = logging.getLogger(__name__)


def health_check(request):
    try:
        connection.ensure_connection()  # Check DB connection
        return JsonResponse({"status": "ok"})
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JsonResponse({"status": "error", "details": str(e)}, status=500)


def custom_404(request, exception=None):
    return JsonResponse({"error": "Resource not found"}, status=404)


def custom_500(request):
    return JsonResponse({"error": "Internal server error"}, status=500)
