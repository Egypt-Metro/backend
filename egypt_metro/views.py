# egypt_metro/views.py

import logging
import os
from django.http import HttpResponse, JsonResponse
from django.db import connection
# from django.utils.timezone import now
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt

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
    """
    Home endpoint that provides an overview of the API.
    Includes links to key features like admin panel, documentation, health checks, and API routes.
    """

    # Get the current time
    current_time = datetime.utcnow()

    # Format the current time with minutes and seconds
    current_date_time = current_time.strftime("%d/%m/%Y %I:%M:%S %p")

    # Calculate uptime dynamically
    uptime_delta = current_time - API_START_TIME
    days, remainder = divmod(uptime_delta.total_seconds(), 86400)  # 86400 seconds in a day
    hours, remainder = divmod(remainder, 3600)  # 3600 seconds in an hour
    minutes, seconds = divmod(remainder, 60)  # 60 seconds in a minute

    # Get the current environment (dev or prod)
    environment = os.getenv("ENVIRONMENT", "dev")  # Default to dev if not set
    logger.debug(f"Current environment: {environment}")

    # Data to return as JSON response
    data = {
        "admin_panel": "/admin/",  # Link to Django admin panel
        "api_documentation": "/docs/",  # Link to API documentation
        "health_check": "/health/",  # Health check endpoint
        "swagger": "/swagger/",     # Swagger API documentation
        "redoc": "/redoc/",     # Redoc API documentation
        "version": "1.0.0",  # Backend version
        "current_date_time": current_date_time,  # Current date and time with minutes and seconds
        "environment": environment,  # Current environment (dev or prod)
        "api_routes": {
            "users": "/api/users/",  # User-related routes
            "register": "/api/users/register/",  # User registration
            "login": "/api/users/login/",  # User login
            "profile": "/api/users/profile/",  # User profile
            "update_profile": "/api/users/profile/update/",  # Update profile
            "token_refresh": "/api/users/token/refresh/",  # Refresh token
            "stations": "/api/stations/",  # Stations-related routes
            "stations_list": "/api/stations/list/",  # List stations
            "trip_details": "/api/stations/trip/<start_station_id>/<end_station_id>/",  # Trip details
            "nearest_station": "/api/stations/nearest/",  # Nearest station
            "precomputed_route": "/api/routes/route/<start_station_id>/<end_station_id>/",  # Precomputed route
            "shortest_route": "/api/routes/shortest/",  # Shortest route
        },
    }

    # Check if browser or API client
    if "text/html" in request.META.get("HTTP_ACCEPT", ""):
        html_content = f"""
            <html>
                <head>
                    <title>Egypt Metro API</title>
                    <style>
                        body {{
                            font-family: Arial, sans-serif;
                            margin: 20px;
                            padding: 0;
                            background-color: #f4f4f4;
                            color: #333;
                        }}
                        h1 {{
                            color: #2c3e50;
                        }}
                        h2 {{
                            color: #34495e;
                        }}
                        ul {{
                            list-style-type: none;
                            padding: 0;
                        }}
                        li {{
                            margin: 10px 0;
                        }}
                        a {{
                            color: #3498db;
                            text-decoration: none;
                        }}
                        a:hover {{
                            text-decoration: underline;
                        }}
                    </style>
                </head>
                <body>
                    <h1>Welcome to Egypt Metro Backend</h1>
                    <p>Version: {data['version']}</p>
                    <p>Date & Time: {data['current_date_time']}</p>
                    <p>Environment: {data['environment']}</p>
                    <h2>Quick Links</h2>
                    <ul>
                        <li><a href="{data['admin_panel']}">Admin Panel</a></li>
                        <li><a href="{data['api_documentation']}">API Documentation</a></li>
                        <li><a href="{data['health_check']}">Health Check</a></li>
                        <li><a href="{data['swagger']}">Swagger API Documentation</a></li>
                        <li><a href="{data['redoc']}">Redoc API Documentation</a></li>
                    </ul>
                    <h2>API Routes</h2>
                    <ul>
            """
        for name, path in data["api_routes"].items():
            html_content += f"<li><a href='{path}'>{name}</a></li>"
        html_content += "</ul></body></html>"

        return HttpResponse(html_content)

    # Return the JSON response with status code 200
    return JsonResponse(data, status=200)


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
