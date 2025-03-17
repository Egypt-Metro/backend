# apps/trains/services/ai_service.py

import io
from PIL import Image
import httpx
import traceback
from django.conf import settings
from typing import Dict, Any
import logging
import asyncio
import json

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.base_url = settings.AI_SERVICE_CONFIG["URL"]
        self.timeout = settings.AI_SERVICE_CONFIG["TIMEOUT"]
        self.max_file_size = settings.AI_SERVICE_CONFIG["MAX_FILE_SIZE"]
        self.allowed_extensions = settings.AI_SERVICE_CONFIG["ALLOWED_EXTENSIONS"]
        self.retry_attempts = settings.AI_SERVICE_CONFIG.get("RETRY_ATTEMPTS", 3)
        self.retry_backoff = settings.AI_SERVICE_CONFIG.get("RETRY_BACKOFF_FACTOR", 0.3)
        self.health_check_endpoints = [
            f"{self.base_url}{settings.AI_SERVICE_CONFIG['ENDPOINTS']['HEALTH_CHECK']}",
            f"{self.base_url}/health",
            f"{self.base_url}/",
            f"{self.base_url}/status",
        ]

    async def validate_image(self, image_data: bytes) -> bool:
        """
        Comprehensive image validation using Pillow

        Args:
            image_data (bytes): Image data to validate

        Returns:
            bool: Whether image is valid
        """
        try:
            # Check file size
            if len(image_data) > self.max_file_size:
                logger.warning(f"Image size exceeds {self.max_file_size} bytes")
                return False

            # Try to open the image
            with Image.open(io.BytesIO(image_data)) as img:
                # Check file format
                file_format = img.format.lower() if img.format else None

                # Map Pillow formats to our allowed extensions
                format_mapping = {
                    'jpeg': 'jpg',
                    'png': 'png',
                    'jpg': 'jpg'
                }

                detected_format = format_mapping.get(file_format)

                if not detected_format or detected_format not in self.allowed_extensions:
                    logger.warning(f"Invalid image type: {file_format}")
                    return False

                # Additional checks (optional)
                if img.width == 0 or img.height == 0:
                    logger.warning("Invalid image dimensions")
                    return False

            return True
        except Exception as e:
            logger.error(f"Image validation error: {e}")
            return False

    async def check_service_health(self, client: httpx.AsyncClient) -> bool:
        """
        Comprehensive health check for AI service with enhanced validation
        """
        for endpoint in self.health_check_endpoints:
            try:
                logger.info(f"Attempting health check on: {endpoint}")

                # Increase timeout for health checks
                response = await client.get(
                    endpoint,
                    timeout=httpx.Timeout(30.0, connect=15.0)
                )

                logger.info(f"Health check response for {endpoint}: {response.status_code}")

                # More flexible status code checking
                if response.status_code in [200, 204]:
                    try:
                        # Parse and validate health response
                        health_data = response.json()

                        # Validate health response structure
                        if isinstance(health_data, dict):
                            # Check for key indicators of operational status
                            if health_data.get('status') == 'operational' or \
                               health_data.get('model_loaded') is True:
                                logger.info(f"Health check successful: {health_data}")
                                return True

                        logger.warning(f"Incomplete health check data: {health_data}")
                    except json.JSONDecodeError:
                        logger.warning(f"Unable to parse health check response from {endpoint}")

                logger.warning(f"Unsuccessful health check on {endpoint}: {response.status_code}")

            except (httpx.ConnectError, httpx.RequestError) as conn_err:
                logger.error(f"Connection error during health check on {endpoint}: {conn_err}")
            except Exception as e:
                logger.error(f"Unexpected error during health check on {endpoint}: {e}")

        return False

    async def process_image(self, image_data: bytes) -> Dict[str, Any]:
        """
        Comprehensive image processing with advanced error handling and retry mechanism
        """
        start_time = asyncio.get_event_loop().time()

        logger.info("=" * 50)
        logger.info("AI Service Image Processing")
        logger.info(f"Image data length: {len(image_data)} bytes")

        # Validate image first
        if not await self.validate_image(image_data):
            return {
                "error": "Invalid image",
                "details": "Image failed validation checks",
                "suggestions": [
                    "Ensure image is not corrupted",
                    f"Max file size is {self.max_file_size / (1024 * 1024)} MB",
                    f"Allowed types: {', '.join(self.allowed_extensions)}",
                ],
            }

        # Construct processing URL
        url = f"{self.base_url}{settings.AI_SERVICE_CONFIG['ENDPOINTS']['PROCESS_IMAGE']}"
        logger.info(f"Attempting AI service connection: {url}")

        # Retry mechanism with exponential backoff
        for attempt in range(self.retry_attempts):
            try:
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(self.timeout, connect=10.0)
                ) as client:
                    # Comprehensive health check
                    health_check_start = asyncio.get_event_loop().time()
                    health_check_result = await self.check_service_health(client)
                    health_check_time = asyncio.get_event_loop().time() - health_check_start

                    logger.info(f"Health check time: {health_check_time:.2f} seconds")

                    if not health_check_result:
                        return {
                            "error": "AI service unavailable",
                            "details": "Comprehensive health check failed",
                            "attempt": attempt + 1,
                            "max_attempts": self.retry_attempts,
                            "health_check_time": health_check_time
                        }

                    # Prepare image for upload
                    files = {"file": ("image.jpg", image_data, "image/jpeg")}

                    # Send image to AI service
                    response = await client.post(url, files=files, timeout=self.timeout)

                    # Performance logging
                    processing_time = asyncio.get_event_loop().time() - start_time
                    logger.info(f"Image processing time: {processing_time:.2f} seconds")

                    # Detailed logging
                    logger.info(f"Response Status: {response.status_code}")

                    # Validate response
                    try:
                        result = response.json()

                        # Comprehensive response validation
                        if not isinstance(result, dict):
                            return {
                                "error": "Invalid response format",
                                "details": f"Expected dict, got {type(result)}",
                                "received_data": result,
                            }

                        # Validate key components of AI response
                        if not all(key in result for key in ["success", "message"]):
                            return {
                                "error": "Incomplete AI service response",
                                "details": "Missing required keys",
                                "received_keys": list(result.keys()),
                            }

                        return result

                    except ValueError as json_err:
                        logger.error(f"JSON parsing error: {json_err}")
                        return {
                            "error": "Failed to parse AI service response",
                            "details": str(json_err),
                            "response_text": response.text,
                        }

            except (httpx.ConnectError, httpx.RequestError) as conn_err:
                logger.error(f"Connection Error (Attempt {attempt + 1}): {conn_err}")

                # Exponential backoff
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_backoff * (2**attempt))
                else:
                    return {
                        "error": "Cannot connect to AI service",
                        "details": str(conn_err),
                        "attempts_made": self.retry_attempts,
                    }

            except Exception as e:
                # Comprehensive unexpected error handling
                error_details = {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "traceback": traceback.format_exc(),
                }

                logger.error(f"Comprehensive error in AI service: {error_details}")

                return {
                    "error": "Unexpected error processing image",
                    "details": error_details,
                    "attempt": attempt + 1,
                }

        # Fallback if all attempts fail
        return {
            "error": "All connection attempts to AI service failed",
            "details": "Maximum retry attempts exhausted",
        }
