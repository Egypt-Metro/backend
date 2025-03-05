# apps/users/utils/decorators.py
import logging
import time
from functools import wraps
from django.core.cache import cache
from rest_framework.exceptions import Throttled

logger = logging.getLogger(__name__)


def rate_limit(requests=5, duration=300):
    """
    Rate limiting decorator
    :param requests: Number of requests allowed
    :param duration: Time window in seconds
    """
    def decorator(func):
        @wraps(func)
        def wrapper(view_instance, request, *args, **kwargs):
            # Create a unique cache key for this user and endpoint
            key = f"rate_limit_{request.user.id}_{request.path}"

            # Get the current requests count and timestamp
            rate_data = cache.get(key, {"count": 0, "reset_time": time.time()})

            # Check if the time window has expired
            current_time = time.time()
            if current_time > rate_data["reset_time"] + duration:
                rate_data = {"count": 0, "reset_time": current_time}

            # Check rate limit
            if rate_data["count"] >= requests:
                raise Throttled(
                    wait=int(rate_data["reset_time"] + duration - current_time)
                )

            # Increment request count
            rate_data["count"] += 1
            cache.set(key, rate_data, duration)

            return func(view_instance, request, *args, **kwargs)
        return wrapper
    return decorator


def log_api_request(func):
    """Log API request and response"""
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
