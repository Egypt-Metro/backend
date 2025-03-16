# metro/views.py

import logging
import os

from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

# API Configuration
API_CONFIG = {
    "VERSION": "1.0.0",  # Define version here instead of using settings
    "NAME": "Egypt Metro API",
    "DESCRIPTION": "Backend API for Egypt Metro System",
    "ENVIRONMENT": os.getenv("ENVIRONMENT", "development"),
    "CONTACT_EMAIL": "admin@metro.com",
}

# API start time (when server starts)
API_START_TIME = datetime.now(timezone.utc)


class APIStatus:
    """Class to manage API status and metadata"""

    @staticmethod
    def format_datetime(dt=None):
        """
        Format datetime in Cairo, Egypt timezone with 12-hour format

        Args:
            dt (datetime, optional): Datetime to format. Defaults to current time.

        Returns:
            str: Formatted datetime string
        """
        if dt is None:
            dt = datetime.now(ZoneInfo("Africa/Cairo"))

        # Convert to Cairo timezone if not already
        cairo_time = dt.astimezone(ZoneInfo("Africa/Cairo"))

        # Format: 3-20-2025 9:15:25 AM
        return cairo_time.strftime("%m-%d-%Y %I:%M:%S %p")

    @staticmethod
    def get_uptime():
        """
        Calculate system uptime

        Returns:
            dict: Uptime breakdown with days, hours, minutes
        """
        try:
            # Get system boot time
            with open("/proc/uptime", "r") as f:
                uptime_seconds = float(f.readline().split()[0])

            # Convert to timedelta
            uptime_delta = timedelta(seconds=uptime_seconds)

            # Break down into days, hours, minutes
            days = uptime_delta.days
            hours, remainder = divmod(uptime_delta.seconds, 3600)
            minutes, _ = divmod(remainder, 60)

            return {"days": days, "hours": hours, "minutes": minutes}
        except Exception as e:
            # Fallback for systems without /proc/uptime or errors
            print(f"Uptime calculation error: {e}")
            return {"days": 0, "hours": 0, "minutes": 0}

    @staticmethod
    def get_environment() -> str:
        """Get current environment"""
        return API_CONFIG["ENVIRONMENT"]


class APIRoutes:
    """Class to manage API routes and documentation"""

    @staticmethod
    def get_routes() -> Dict[str, Dict[str, Any]]:
        """Get all API routes with metadata"""
        return {
            "authentication": {
                "title": "Authentication",
                "routes": {
                    "login": "/api/users/login/",
                    "register": "/api/users/register/",
                    "profile": "/api/users/profile/",
                    "token_refresh": "/api/users/token/refresh/",
                },
            },
            "stations": {
                "title": "Stations",
                "routes": {
                    "list": "/api/stations/list/",
                    "nearest": "/api/stations/nearest/",
                    "trip_details": "/api/stations/trip/{start_id}/{end_id}/",
                },
            },
            "trains": {
                "title": "Trains",
                "routes": {
                    "list": "/api/trains/",
                    "schedules": "/api/trains/get-schedules/",
                    "crowd_level": "/api/trains/{id}/update-crowd-level/",
                },
            },
            "routes": {
                "title": "Routes",
                "routes": {
                    "find": "/api/routes/find/",
                    "shortest": "/api/routes/shortest/",
                },
            },
        }


class UIComponents:
    """Class to manage UI components and styling"""

    @staticmethod
    def get_css() -> str:
        """Get CSS styles"""
        return """
            :root {
                --primary-color: #2c3e50;
                --secondary-color: #34495e;
                --accent-color: #3498db;
                --background-color: #f4f4f4;
                --text-color: #333;
                --success-color: #2ecc71;
                --error-color: #e74c3c;
                --border-radius: 8px;
                --box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }

            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: var(--background-color);
                color: var(--text-color);
                line-height: 1.6;
            }

            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
            }

            .header {
                background-color: var(--primary-color);
                color: white;
                padding: 20px;
                border-radius: var(--border-radius);
                margin-bottom: 20px;
                box-shadow: var(--box-shadow);
            }

            .header h1 {
                margin: 0;
                font-size: 2em;
            }

            .section {
                background: white;
                padding: 20px;
                border-radius: var(--border-radius);
                margin-bottom: 20px;
                box-shadow: var(--box-shadow);
            }

            .route-group {
                margin-bottom: 30px;
            }

            .route-list {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
                gap: 15px;
            }

            .route-item {
                background: white;
                padding: 15px;
                border-radius: var(--border-radius);
                border-left: 4px solid var(--accent-color);
                box-shadow: var(--box-shadow);
                transition: transform 0.2s;
            }

            .route-item:hover {
                transform: translateY(-2px);
            }

            .status-badge {
                display: inline-block;
                padding: 4px 8px;
                border-radius: 4px;
                background-color: var(--success-color);
                color: white;
                font-weight: bold;
            }

            .api-info {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 10px;
            }

            code {
                background: #f8f9fa;
                padding: 2px 6px;
                border-radius: 4px;
                font-family: 'Courier New', Courier, monospace;
            }

            @media (max-width: 768px) {
                .route-list {
                    grid-template-columns: 1fr;
                }

                .api-info {
                    flex-direction: column;
                    align-items: flex-start;
                }
            }
        """


@csrf_exempt
def home(request) -> HttpResponse:
    """Home endpoint with API overview"""

    # Get current status
    current_time = datetime.now(ZoneInfo("Africa/Cairo"))
    uptime = APIStatus.get_uptime()
    environment = APIStatus.get_environment()

    # Prepare data
    data = {
        "name": API_CONFIG["NAME"],
        "version": API_CONFIG["VERSION"],
        "description": API_CONFIG["DESCRIPTION"],
        "environment": environment,
        "current_time": APIStatus.format_datetime(current_time),
        "uptime": uptime,
        "status": "operational",
        "contact": API_CONFIG["CONTACT_EMAIL"],
        "documentation": {
            "Swagger UI": "/swagger/",
            "ReDoc": "/redoc/",
            "API Docs": "/api/docs/",
            "Postman Collection": "/api/schema/",
            "OpenAPI JSON": "/swagger.json",
        },
        "routes": APIRoutes.get_routes(),
        "language": "en",
    }

    # Return HTML for browsers
    if "text/html" in request.META.get("HTTP_ACCEPT", ""):
        context = {"data": data, "css": UIComponents.get_css()}
        html_content = render_to_string("metro/home.html", context)
        return HttpResponse(html_content)

    # Return JSON for API clients
    return JsonResponse(data)


def health_check(request):
    """
    Comprehensive health check endpoint for Render

    Checks:
    - Database connectivity
    - Cache functionality
    - Environment configuration
    - Basic system resources
    """
    try:
        # Database check
        database_status = check_database_connection()

        # Cache check
        cache_status = check_cache_functionality()

        # Environment checks
        env_checks = check_environment_configuration()

        # System resource checks
        system_resources = check_system_resources()

        # Prepare response
        response_data = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {
                "database": database_status,
                "cache": cache_status,
                "environment": env_checks,
                "system_resources": system_resources,
            },
            "version": get_app_version(),
            "deployment_info": get_deployment_info(),
        }

        # Log successful health check
        logger.info("Health check passed successfully")

        return JsonResponse(response_data)

    except Exception as e:
        # Log detailed error
        logger.error(f"Health check failed: {str(e)}", exc_info=True)

        return JsonResponse(
            {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            status=500,
        )


def check_database_connection():
    """
    Check database connectivity
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return "operational"
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}")
        return f"error: {str(e)}"


def check_cache_functionality():
    """
    Verify cache is working
    """
    try:
        # Try to set and get a test key
        test_key = "health_check_test"
        cache.set(test_key, "working", 10)  # 10-second timeout
        value = cache.get(test_key)

        if value != "working":
            return "not responding"

        return "operational"
    except Exception as e:
        logger.error(f"Cache check failed: {str(e)}")
        return f"error: {str(e)}"


def check_environment_configuration():
    """
    Check critical environment configurations
    """
    checks = {}

    # Check critical settings
    critical_settings = ["SECRET_KEY", "DEBUG", "ALLOWED_HOSTS", "DATABASE_URL"]

    for setting in critical_settings:
        try:
            value = getattr(settings, setting, None)
            checks[setting.lower()] = "configured" if value else "not set"
        except Exception as e:
            checks[setting.lower()] = f"error: {str(e)}"

    return checks


def check_system_resources():
    """
    Basic system resource checks
    """
    try:
        # Check disk space
        total, used, free = get_disk_usage()

        return {
            "disk_total": f"{total} GB",
            "disk_used": f"{used} GB ({used / total * 100:.2f}%)",
            "disk_free": f"{free} GB",
            "memory": get_memory_usage(),
        }
    except Exception as e:
        logger.error(f"System resource check failed: {str(e)}")
        return {"error": str(e)}


def get_disk_usage():
    """
    Get disk usage statistics
    """
    try:
        import shutil

        # Get the directory of the current script
        directory = os.path.dirname(os.path.abspath(__file__))

        # Get disk usage
        total, used, free = shutil.disk_usage(directory)

        # Convert to GB
        return (
            total // (1024 * 1024 * 1024),
            used // (1024 * 1024 * 1024),
            free // (1024 * 1024 * 1024),
        )
    except Exception as e:
        logger.error(f"Disk usage check failed: {str(e)}")
        return (0, 0, 0)


def get_memory_usage():
    """
    Get memory usage
    """
    try:
        import psutil

        memory = psutil.virtual_memory()
        return {
            "total": f"{memory.total / (1024 * 1024 * 1024):.2f} GB",
            "available": f"{memory.available / (1024 * 1024 * 1024):.2f} GB",
            "used_percent": f"{memory.percent}%",
        }
    except ImportError:
        return "psutil not available"
    except Exception as e:
        return f"error: {str(e)}"


def get_app_version():
    """
    Get application version
    """
    try:
        # You can replace this with your actual version tracking method
        import subprocess

        # Get latest git commit hash
        commit_hash = (
            subprocess.check_output(["git", "rev-parse", "--short", "HEAD"])
            .decode("ascii")
            .strip()
        )

        return commit_hash
    except Exception:
        # Fallback to a static version or environment variable
        return os.environ.get("APP_VERSION", "unknown")


def get_deployment_info():
    """
    Get deployment-specific information
    """
    return {
        "environment": os.environ.get("ENVIRONMENT", "unknown"),
        "python_version": os.environ.get("PYTHON_VERSION", "unknown"),
        "deployed_at": os.environ.get("DEPLOYED_AT", "unknown"),
    }


def custom_404(request, exception: Optional[Exception] = None) -> JsonResponse:
    """Custom 404 handler"""
    return JsonResponse(
        {"error": "Resource not found", "path": request.path}, status=404
    )


def custom_500(request) -> JsonResponse:
    """Custom 500 handler"""
    return JsonResponse(
        {
            "error": "Internal server error",
            "request_id": request.META.get("HTTP_X_REQUEST_ID"),
        },
        status=500,
    )
