# apps/users/utils/decorators.py
import logging
from functools import wraps

logger = logging.getLogger(__name__)


def log_api_request(func):
    @wraps(func)
    def wrapper(view_instance, request, *args, **kwargs):
        logger.info(
            f"API Request - Method: {request.method}, "
            f"Path: {request.path}, "
            f"User: {request.user}"
        )
        response = func(view_instance, request, *args, **kwargs)
        logger.info(
            f"API Response - Status: {response.status_code}, "
            f"Path: {request.path}"
        )
        return response
    return wrapper
