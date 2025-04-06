# apps/trains/services/ai_service.py

from typing import Any, Dict
import httpx
from django.conf import settings
import logging
import asyncio
import json

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.base_url = settings.AI_SERVICE_CONFIG["URL"]
        self.timeout = settings.AI_SERVICE_CONFIG.get("TIMEOUT", 600)
        self.max_file_size = settings.AI_SERVICE_CONFIG["MAX_FILE_SIZE"]
        self.allowed_extensions = settings.AI_SERVICE_CONFIG["ALLOWED_EXTENSIONS"]
        self.retry_attempts = settings.AI_SERVICE_CONFIG.get("RETRY_ATTEMPTS", 5)
        self.retry_backoff = settings.AI_SERVICE_CONFIG.get("RETRY_BACKOFF_FACTOR", 1.0)

    async def _check_service_health(self, client: httpx.AsyncClient) -> bool:
        """Check if the AI service is healthy"""
        try:
            response = await client.get(
                f"{self.base_url}/health",
                timeout=httpx.Timeout(10.0)
            )
            return response.status_code == 200 and response.json().get("status") == "ok"
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False

    async def process_image(self, image_data: bytes) -> Dict[str, Any]:
        """Process image with comprehensive error handling and retries"""
        start_time = asyncio.get_event_loop().time()

        # Configure client with optimal settings
        client_config = {
            "timeout": httpx.Timeout(
                timeout=float(self.timeout),
                connect=30.0,
                read=float(self.timeout),
                write=30.0
            ),
            "limits": httpx.Limits(
                max_keepalive_connections=5,
                max_connections=10,
                keepalive_expiry=30.0
            ),
            "headers": {
                "Accept": "application/json",
                "User-Agent": "MetroAI/1.0"
            }
        }

        for attempt in range(self.retry_attempts):
            try:
                async with httpx.AsyncClient(**client_config) as client:
                    # Check service health
                    is_healthy = await self._check_service_health(client)
                    if not is_healthy and attempt < self.retry_attempts - 1:
                        backoff_time = self.retry_backoff * (2 ** attempt)
                        logger.warning(f"Service unhealthy, waiting {backoff_time:.1f} seconds before retry...")
                        await asyncio.sleep(backoff_time)
                        continue

                    # Prepare and send request
                    files = {"file": ("image.jpg", image_data, "image/jpeg")}
                    logger.info(f"Sending request (Attempt {attempt + 1}/{self.retry_attempts})")

                    response = await client.post(
                        f"{self.base_url}/process_image/",
                        files=files
                    )

                    processing_time = asyncio.get_event_loop().time() - start_time
                    logger.info(f"Request completed in {processing_time:.1f} seconds (Status: {response.status_code})")

                    # Handle different response statuses
                    if response.status_code == 200:
                        try:
                            result = response.json()
                            if isinstance(result, dict) and "message" in result:
                                return {
                                    "success": True,
                                    "message": result["message"],
                                    "processing_time": processing_time,
                                    "attempt": attempt + 1
                                }
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON parsing error: {e}")

                    elif response.status_code == 503:
                        if attempt < self.retry_attempts - 1:
                            backoff_time = self.retry_backoff * (2 ** attempt)
                            logger.info(f"Service unavailable, retrying in {backoff_time:.1f} seconds...")
                            await asyncio.sleep(backoff_time)
                            continue
                        else:
                            return {
                                "success": False,
                                "error": "Service unavailable",
                                "details": "AI service is temporarily unavailable",
                                "suggestions": [
                                    "Please try again in a few minutes",
                                    "Service is under high load",
                                    "Contact support if the issue persists"
                                ]
                            }

                    # If we get here, it's an unexpected status code
                    if attempt < self.retry_attempts - 1:
                        backoff_time = self.retry_backoff * (2 ** attempt)
                        await asyncio.sleep(backoff_time)
                        continue

            except httpx.TimeoutException as e:
                logger.error(f"Timeout on attempt {attempt + 1}: {e}")
                if attempt < self.retry_attempts - 1:
                    backoff_time = self.retry_backoff * (2 ** attempt)
                    await asyncio.sleep(backoff_time)
                    continue

                return {
                    "success": False,
                    "error": "Request timeout",
                    "details": "The AI service is taking too long to respond",
                    "suggestions": [
                        "The service might be under heavy load",
                        "Try again in a few minutes",
                        "Try with a smaller image"
                    ]
                }

            except Exception as e:
                logger.error(f"Error on attempt {attempt + 1}: {str(e)}")
                if attempt < self.retry_attempts - 1:
                    backoff_time = self.retry_backoff * (2 ** attempt)
                    await asyncio.sleep(backoff_time)
                    continue

        # If we get here, all attempts failed
        return {
            "success": False,
            "error": "AI service error",
            "details": "Maximum retry attempts exceeded",
            "suggestions": [
                "The service might be experiencing issues",
                "Try again later",
                "Contact support if the issue persists"
            ]
        }
