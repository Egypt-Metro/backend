import logging
from django.http import JsonResponse
from django.db import connection
# from django.utils.timezone import now
from datetime import datetime
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

# Define the API's start time globally (when the server starts)
API_START_TIME = datetime.utcnow()


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

    # Format uptime
    uptime = f"{int(days)} days, {int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds"

    # Data to return as JSON response
    data = {
        "message": "Welcome to Egypt Metro Backend",
        "status": "OK",  # Status indicating the API is operational
        "admin_panel": "/admin/",  # Link to Django admin panel
        "api_documentation": "/docs/",  # Link to API documentation
        "health_check": "/health/",  # Health check endpoint
        "swagger": "/swagger/",     # Swagger API documentation
        "redoc": "/redoc/",     # Redoc API documentation
        "version": "1.0.0",  # Backend version
        "uptime": uptime,  # Dynamically calculated uptime
        "current_date_time": current_date_time,  # Current date and time with minutes and seconds
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
        },
    }

    # Check if browser or API client
    if "text/html" in request.META.get("HTTP_ACCEPT", ""):
        html_content = f"""
        <html>
            <head>
                <title>Egypt Metro API</title>
            </head>
            <body>
                <h1>Welcome to Egypt Metro Backend</h1>
                <p>Status: {data['status']}</p>
                <p>Version: {data['version']}</p>
                <p>Uptime: {data['uptime']}</p>
                <p>Current Date & Time: {data['current_date_time']}</p>
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
        logger.error("Health check failed", exc_info=e)
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


def custom_404(request, exception=None):
    return JsonResponse({"error": "Resource not found"}, status=404)


def custom_500(request):
    return JsonResponse({"error": "Internal server error"}, status=500)
