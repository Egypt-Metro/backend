# egypt_metro/views.py

import logging
from django.http import JsonResponse
from django.shortcuts import render
from django.db import connection
# from django.utils.timezone import now
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt

from egypt_metro import settings

logger = logging.getLogger(__name__)

# Define the API's start time globally (when the server starts)
API_START_TIME = datetime.utcnow()


def log_session_data(request):
    if request.user.is_authenticated:
        logger.debug(f"Session ID: {request.session.session_key}")
        logger.debug(f"Session Data: {request.session.items()}")
    else:
        logger.debug("User is not authenticated")


@csrf_exempt
def home(request):
    context = {
        'version': '1.0.0',
        'environment': settings.ENVIRONMENT,
        'current_time': datetime.now().strftime('%d/%m/%Y %I:%M:%S %p'),
        'metro_lines': [
            {
                'name': 'First Line',
                'color': '#FF0000',
                'stations': 35,
                'start': 'Helwan',
                'end': 'New El-Marg'
            },
            {
                'name': 'Second Line',
                'color': '#008000',
                'stations': 20,
                'start': 'El-Mounib',
                'end': 'Shubra El-Kheima'
            },
            {
                'name': 'Third Line',
                'color': '#0000FF',
                'stations': 34,
                'start': 'Adly Mansour',
                'end': 'Rod al-Farag Axis'
            }
        ]
    }
    return render(request, 'home.html', context)


def health_check(request):
    """
    Health check view to verify the application is running properly.
    """
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")

        # Return a success response
        return JsonResponse({"status": "ok"}, status=200)

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return JsonResponse({"status": "error", "message": "Database connectivity issue"}, status=500)


def custom_404(request, exception=None):
    return JsonResponse({"error": "Resource not found"}, status=404)


def custom_500(request):
    return JsonResponse({"error": "Internal server error"}, status=500)


# def check_environment(request):
#     """
#     View to check the current environment (dev or prod).
#     """
#     try:
#         # Get the environment (default to 'dev' if not set)
#         environment = os.getenv("ENVIRONMENT", "dev")  # Default to dev if not set
#         logger.debug(f"Current environment: {environment}")

#         # Respond with JSON, which is a standard format for APIs
#         response_data = {
#             "environment": environment,
#             "status": "success",
#         }
#         return JsonResponse(response_data)

#     except Exception as e:
#         # Log the error for debugging purposes
#         logger.error(f"Error in check_environment view: {str(e)}")

#         # Return an error response in case of failure
#         return JsonResponse(
#             {"error": "Unable to determine the environment", "status": "fail"},
#             status=500,
#         )
