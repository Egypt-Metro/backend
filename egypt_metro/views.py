# import logging
from django.http import JsonResponse
# from django.db import connection

# logger = logging.getLogger(__name__)


# def health_check(request):
#     """
#     Health check view to verify the application is running properly.
#     """
#     try:
#         # Check database connection
#         with connection.cursor() as cursor:
#             cursor.execute("SELECT 1;")

#         # Return a success response
#         return JsonResponse({"status": "ok"}, status=200)

#     except Exception as e:
#         logger.error("Health check failed", exc_info=e)
#         return JsonResponse({"status": "error", "message": str(e)}, status=500)


def custom_404(request, exception=None):
    return JsonResponse({"error": "Resource not found"}, status=404)


def custom_500(request):
    return JsonResponse({"error": "Internal server error"}, status=500)
