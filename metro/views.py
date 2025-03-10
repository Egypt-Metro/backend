# metro/views.py

import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from django.db import connection
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

# API Configuration
API_CONFIG = {
    'VERSION': '1.0.0',  # Define version here instead of using settings
    'NAME': 'Egypt Metro API',
    'DESCRIPTION': 'Backend API for Egypt Metro System',
    'ENVIRONMENT': os.getenv('ENVIRONMENT', 'development'),
    'CONTACT_EMAIL': 'contact@metro.com',
}

# API start time (when server starts)
API_START_TIME = datetime.now(timezone.utc)


class APIStatus:
    """Class to manage API status and metadata"""

    @staticmethod
    def get_uptime() -> Dict[str, int]:
        """Calculate API uptime"""
        current_time = datetime.now(timezone.utc)
        delta = current_time - API_START_TIME

        return {
            'days': delta.days,
            'hours': delta.seconds // 3600,
            'minutes': (delta.seconds % 3600) // 60,
            'seconds': delta.seconds % 60
        }

    @staticmethod
    def get_environment() -> str:
        """Get current environment"""
        return API_CONFIG['ENVIRONMENT']

    @staticmethod
    def format_datetime(dt: datetime) -> str:
        """Format datetime for display"""
        return dt.strftime("%Y-%m-%d %H:%M:%S %Z")


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
                    "token_refresh": "/api/users/token/refresh/"
                }
            },
            "stations": {
                "title": "Stations",
                "routes": {
                    "list": "/api/stations/list/",
                    "nearest": "/api/stations/nearest/",
                    "trip_details": "/api/stations/trip/{start_id}/{end_id}/"
                }
            },
            "trains": {
                "title": "Trains",
                "routes": {
                    "list": "/api/trains/",
                    "schedules": "/api/trains/get-schedules/",
                    "crowd_level": "/api/trains/{id}/update-crowd-level/"
                }
            },
            "routes": {
                "title": "Routes",
                "routes": {
                    "find": "/api/routes/find/",
                    "shortest": "/api/routes/shortest/"
                }
            }
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
    current_time = datetime.now(timezone.utc)
    uptime = APIStatus.get_uptime()
    environment = APIStatus.get_environment()

    # Prepare data
    data = {
        "name": API_CONFIG['NAME'],
        "version": API_CONFIG['VERSION'],
        "description": API_CONFIG['DESCRIPTION'],
        "environment": environment,
        "current_time": APIStatus.format_datetime(current_time),
        "uptime": uptime,
        "status": "operational",
        "contact": API_CONFIG['CONTACT_EMAIL'],
        "documentation": {
            "swagger": "/swagger/",
            "redoc": "/redoc/",
            "api_docs": "/api/docs/"
        },
        "routes": APIRoutes.get_routes()
    }

    # Return HTML for browsers
    if "text/html" in request.META.get("HTTP_ACCEPT", ""):
        context = {
            "data": data,
            "css": UIComponents.get_css()
        }
        html_content = render_to_string('metro/home.html', context)
        return HttpResponse(html_content)

    # Return JSON for API clients
    return JsonResponse(data)


def health_check(request) -> JsonResponse:
    """Health check endpoint"""
    try:
        # Check database
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        return JsonResponse({
            "status": "healthy",
            "checks": {
                "database": "operational",
                "api": "operational"
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        return JsonResponse({
            "status": "unhealthy",
            "error": str(e)
        }, status=500)


def custom_404(request, exception: Optional[Exception] = None) -> JsonResponse:
    """Custom 404 handler"""
    return JsonResponse({
        "error": "Resource not found",
        "path": request.path
    }, status=404)


def custom_500(request) -> JsonResponse:
    """Custom 500 handler"""
    return JsonResponse({
        "error": "Internal server error",
        "request_id": request.META.get('HTTP_X_REQUEST_ID')
    }, status=500)
