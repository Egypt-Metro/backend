# apps/dashboard/services/ai_service.py

import io
from PIL import Image
import httpx
import traceback
from django.conf import settings
from typing import Dict, Any
import logging
import asyncio

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.base_url = settings.AI_SERVICE_CONFIG["URL"]
        self.timeout = settings.AI_SERVICE_CONFIG["TIMEOUT"]
        self.max_file_size = settings.AI_SERVICE_CONFIG["MAX_FILE_SIZE"]
        self.allowed_extensions = settings.AI_SERVICE_CONFIG["ALLOWED_EXTENSIONS"]
        self.retry_attempts = settings.AI_SERVICE_CONFIG.get("RETRY_ATTEMPTS", 3)
        self.retry_backoff = settings.AI_SERVICE_CONFIG.get("RETRY_BACKOFF_FACTOR", 0.3)

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
        Comprehensive health check for AI service

        Args:
            client (httpx.AsyncClient): HTTP client to use for health check

        Returns:
            bool: Whether service is healthy
        """
        health_endpoints = [
            f"{self.base_url}/health",
            f"{self.base_url}/",
            f"{self.base_url}/status",
        ]

        for endpoint in health_endpoints:
            try:
                response = await client.get(endpoint, timeout=10.0)
                logger.info(f"Health check on {endpoint}: {response.status_code}")

                # Accept 200 or 204 as valid responses
                if response.status_code in [200, 204]:
                    # Optional: Parse response for additional info
                    try:
                        health_data = response.json()
                        logger.info(f"Health check details: {health_data}")
                    except Exception:
                        pass
                    return True
            except Exception as e:
                logger.warning(f"Health check failed for {endpoint}: {e}")

        return False

    async def process_image(self, image_data: bytes) -> Dict[str, Any]:
        """
        Comprehensive image processing with advanced error handling and retry mechanism

        Args:
            image_data (bytes): Image data to process

        Returns:
            Dict with processing results or error details
        """
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

        # Construct URLs
        url = (
            f"{self.base_url}{settings.AI_SERVICE_CONFIG['ENDPOINTS']['PROCESS_IMAGE']}"
        )

        # Logging connection attempt
        logger.info(f"Attempting AI service connection: {url}")

        # Retry mechanism with exponential backoff
        for attempt in range(self.retry_attempts):
            try:
                async with httpx.AsyncClient(
                    timeout=httpx.Timeout(30.0, connect=10.0)
                ) as client:
                    # Comprehensive health check
                    if not await self.check_service_health(client):
                        return {
                            "error": "AI service unavailable",
                            "details": "Service health check failed",
                            "attempt": attempt + 1,
                            "max_attempts": self.retry_attempts,
                        }

                    # Prepare image for upload
                    files = {"file": ("image.jpg", image_data, "image/jpeg")}

                    # Send image to AI service
                    response = await client.post(url, files=files, timeout=self.timeout)

                    # Detailed logging
                    logger.info(f"Response Status: {response.status_code}")
                    logger.info(f"Response Headers: {response.headers}")

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

    def debug_connection(self) -> Dict[str, Any]:
        """
        Comprehensive debugging method for AI service connection

        Returns:
            Dict with detailed connection diagnostics
        """
        import socket
        import ssl

        debug_info = {
            "service_url": self.base_url,
            "max_file_size": f"{self.max_file_size / (1024 * 1024)} MB",
            "allowed_extensions": self.allowed_extensions,
            "network_diagnostics": {},
        }

        try:
            # Parse URL
            from urllib.parse import urlparse

            parsed_url = urlparse(self.base_url)

            # DNS Resolution
            try:
                ip_addresses = socket.gethostbyname_ex(parsed_url.hostname)
                debug_info["network_diagnostics"]["dns_resolution"] = {
                    "hostname": parsed_url.hostname,
                    "ip_addresses": ip_addresses[2],
                }
            except Exception as dns_err:
                debug_info["network_diagnostics"]["dns_resolution_error"] = str(dns_err)

            # SSL/TLS Check
            try:
                context = ssl.create_default_context()
                with socket.create_connection(
                    (parsed_url.hostname, parsed_url.port or 443)
                ) as sock:
                    with context.wrap_socket(
                        sock, server_hostname=parsed_url.hostname
                    ) as secure_sock:
                        debug_info["network_diagnostics"]["ssl_check"] = {
                            "protocol": secure_sock.version(),
                            "cipher": secure_sock.cipher(),
                        }
            except Exception as ssl_err:
                debug_info["network_diagnostics"]["ssl_error"] = str(ssl_err)

        except Exception as e:
            debug_info["debug_error"] = str(e)

        return debug_info
