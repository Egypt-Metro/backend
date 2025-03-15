import httpx
from django.conf import settings
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.base_url = settings.AI_SERVICE_CONFIG['URL']
        self.timeout = settings.AI_SERVICE_CONFIG['TIMEOUT']
        self.max_file_size = settings.AI_SERVICE_CONFIG['MAX_FILE_SIZE']
        self.allowed_extensions = settings.AI_SERVICE_CONFIG['ALLOWED_EXTENSIONS']

    async def validate_image(self, image_data: bytes) -> bool:
        """
        Validate image before sending to AI service
        """
        # Check file size
        if len(image_data) > self.max_file_size:
            logger.warning(f"Image size exceeds {self.max_file_size} bytes")
            return False

        # You could add more validation like checking file extension
        return True

    async def process_image(self, image_data: bytes) -> Dict[str, Any]:
        """
        Send image to AI service for processing

        Args:
            image_data (bytes): Image data to process

        Returns:
            Dict with processing results or error
        """
        try:
            # Validate image first
            if not await self.validate_image(image_data):
                return {"error": "Invalid image"}

            # Construct full URL
            url = f"{self.base_url}{settings.AI_SERVICE_CONFIG['ENDPOINTS']['PROCESS_IMAGE']}"

            # Async HTTP client for non-blocking request
            async with httpx.AsyncClient() as client:
                # Prepare multipart form data
                files = {'file': ('image.jpg', image_data, 'image/jpeg')}

                # Send POST request
                response = await client.post(
                    url,
                    files=files,
                    timeout=self.timeout
                )

                # Raise exception for bad HTTP responses
                response.raise_for_status()

                # Parse and return JSON response
                result = response.json()

                # Log successful response
                logger.info(f"AI Service Response: {result}")

                return result

        except httpx.HTTPStatusError as http_err:
            # Handle HTTP errors (4xx, 5xx)
            logger.error(f"HTTP Error: {http_err}")
            return {
                "error": "AI service communication error",
                "details": str(http_err)
            }
        except httpx.RequestError as req_err:
            # Handle network-related errors
            logger.error(f"Request Error: {req_err}")
            return {
                "error": "Network error connecting to AI service",
                "details": str(req_err)
            }
        except Exception as e:
            # Catch-all for unexpected errors
            logger.error(f"Unexpected error: {e}")
            return {
                "error": "Unexpected error processing image",
                "details": str(e)
            }
