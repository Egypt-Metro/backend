import requests
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class HardwareService:
    """Service to communicate with ESP8266"""

    def __init__(self):
        self.esp_base_url = getattr(settings, 'ESP8266_BASE_URL', 'http://192.168.4.1')

    def send_validation_result(self, is_valid: bool) -> bool:
        """
        Sends validation result to ESP8266
        """
        try:
            endpoint = '/success' if is_valid else '/fail'
            response = requests.get(
                f"{self.esp_base_url}{endpoint}",
                timeout=2
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send command to ESP8266: {str(e)}")
            return False
