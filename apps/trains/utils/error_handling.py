# apps/trains/utils/error_handling.py

from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)


class APIError(Exception):
    def __init__(self, message, status_code=status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def api_error_handler(func):
    """Decorator for handling API errors"""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except APIError as e:
            logger.warning(f"API Error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=e.status_code
            )
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return Response(
                {'error': 'An unexpected error occurred'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    return wrapper
