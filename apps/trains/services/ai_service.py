# apps/trains/services/ai_service.py

import httpx
from django.conf import settings
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class AIService:
    def __init__(self):
        self.base_url = settings.AI_SERVICE_CONFIG['URL']
        self.timeout = settings.AI_SERVICE_CONFIG['TIMEOUT']

    async def process_image(self, image_data: bytes) -> Dict[str, Any]:
        """Send image to AI service for processing"""
        try:
            url = f"{self.base_url}{settings.AI_SERVICE_CONFIG['ENDPOINTS']['PROCESS_IMAGE']}"

            async with httpx.AsyncClient() as client:
                files = {'file': ('image.jpg', image_data, 'image/jpeg')}
                response = await client.post(
                    url,
                    files=files,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return response.json()

        except httpx.HTTPError as e:
            logger.error(f"HTTP error while processing image: {str(e)}")
            return {"error": "AI service communication error"}
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return {"error": str(e)}
