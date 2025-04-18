# metro/views.py

import importlib
import logging
import os

import platform
import sys
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

# API Configuration
API_CONFIG = {
    "VERSION": "1.0.0",  # Define version here instead of using settings
    "NAME": "Egypt Metro",
    "DESCRIPTION": "Egypt Metro Backend",
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
    Robust health check endpoint with error handling
    """
    try:
        # Comprehensive checks
        checks = {
            "python_version": sys.version,
            "environment": os.environ.get('ENVIRONMENT', 'unknown'),
        }

        # Check critical dependencies
        critical_dependencies = [
            'django', 'psycopg2', 'djangorestframework',
            'python-magic', 'pillow'
        ]

        dependency_checks = {}
        for dep in critical_dependencies:
            try:
                importlib.import_module(dep.replace('-', '_'))
                dependency_checks[dep] = 'installed'
            except ImportError:
                dependency_checks[dep] = 'missing'
                logger.warning(f"Dependency not found: {dep}")

        checks['dependencies'] = dependency_checks

        # Database check
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            database_status = 'operational'
        except Exception as db_error:
            database_status = f'error: {str(db_error)}'
            logger.error(f"Database check failed: {db_error}")

        # Combine dependency statuses and database status
        all_statuses = list(dependency_checks.values()) + [database_status]

        # Comprehensive response
        response_data = {
            "status": "healthy" if all(
                status == 'installed' or status == 'operational'
                for status in all_statuses
            ) else "partially_healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {
                **checks,
                "database": database_status
            }
        }

        logger.info("Health check passed successfully")
        return JsonResponse(response_data)

    except Exception as e:
        logger.error(f"Comprehensive health check failed: {e}", exc_info=True)
        return JsonResponse({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, status=500)


def check_dependencies(request):
    """
    Comprehensive dependency check
    """
    dependencies = {}

    # List of dependencies to check
    check_list = [
        'django', 'psycopg2', 'djangorestframework',
        'python-magic', 'pillow', 'gunicorn'
    ]

    for dep in check_list:
        try:
            # Handle different module naming conventions
            module_name = dep.replace('-', '_')

            # Special handling for some libraries
            if module_name == 'djangorestframework':
                module_name = 'rest_framework'

            module = importlib.import_module(module_name)

            # Try to get version
            try:
                version = module.__version__
            except AttributeError:
                try:
                    version = getattr(module, 'VERSION', 'unknown')
                    if isinstance(version, tuple):
                        version = '.'.join(map(str, version))
                except Exception:
                    version = 'unknown'

            dependencies[dep] = {
                'installed': True,
                'version': version
            }
        except ImportError:
            dependencies[dep] = {
                'installed': False,
                'version': None
            }
        except Exception as e:
            dependencies[dep] = {
                'installed': False,
                'error': str(e)
            }

    return JsonResponse({
        'dependencies': dependencies,
        'python_version': sys.version,
        'platform': platform.platform(),
        'system': {
            'os': platform.system(),
            'release': platform.release(),
            'machine': platform.machine()
        }
    })


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
