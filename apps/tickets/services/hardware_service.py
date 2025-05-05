import logging
from django.core.cache import cache

logger = logging.getLogger(__name__)


class HardwareService:
    """Service to provide real-time ticket validation status for hardware gates"""

    # Cache key for storing the latest validation result
    VALIDATION_STATUS_KEY = "latest_ticket_validation_status"
    # Cache timeout in seconds (5 minutes)
    CACHE_TIMEOUT = 300

    def send_validation_result(self, is_valid: bool) -> bool:
        """
        Stores validation result for hardware to retrieve
        This is called whenever a ticket is validated
        """
        try:
            # Store result (1 for valid, 0 for invalid)
            result_value = "1" if is_valid else "0"
            cache.set(self.VALIDATION_STATUS_KEY, result_value, self.CACHE_TIMEOUT)

            logger.info(f"Set hardware gate validation result: {'VALID' if is_valid else 'INVALID'}")
            return True
        except Exception as e:
            logger.error(f"Failed to set hardware validation result: {str(e)}")
            return False

    @classmethod
    def get_latest_validation_result(cls):
        """Get the latest validation result from cache"""
        result = cache.get(cls.VALIDATION_STATUS_KEY)
        if result is None:
            # Initialize with default "0" if not set
            cache.set(cls.VALIDATION_STATUS_KEY, "0", cls.CACHE_TIMEOUT)
            return "0"
        return result
