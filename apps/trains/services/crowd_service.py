# apps/trains/services/crowd_service.py

import httpx
from django.conf import settings
from typing import Dict, Any
import logging
from ..models.train import TrainCar
from ..constants.choices import CrowdLevel, CROWD_THRESHOLDS

logger = logging.getLogger(__name__)


class CrowdDetectionService:
    """Service for detecting and managing crowd levels in train cars"""

    def __init__(self):
        self.ai_service_url = settings.AI_SERVICE_CONFIG['URL']
        self.process_image_endpoint = settings.AI_SERVICE_CONFIG['ENDPOINTS']['PROCESS_IMAGE']
        self.timeout = settings.AI_SERVICE_CONFIG['TIMEOUT']
        self.headers = {
            'Accept': 'application/json',
        }
        # Add API key if configured
        if hasattr(settings, 'AI_SERVICE_API_KEY'):
            self.headers['X-API-Key'] = settings.AI_SERVICE_API_KEY

    async def process_image(self, image_data: bytes) -> Dict[str, Any]:
        """
        Send image to AI service and get passenger count

        Args:
            image_data: Raw bytes of the image file

        Returns:
            Dict containing either the passenger count or error message
        """
        try:
            async with httpx.AsyncClient() as client:
                files = {'file': ('image.jpg', image_data, 'image/jpeg')}
                url = f"{self.ai_service_url}{self.process_image_endpoint}"

                logger.info(f"Sending image to AI service: {url}")

                response = await client.post(
                    url,
                    files=files,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()

                result = response.json()
                logger.info(f"AI service response: {result}")

                return result

        except httpx.HTTPError as e:
            logger.error(f"HTTP error processing image: {str(e)}")
            return {"error": "AI service communication error", "details": str(e)}
        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            return {"error": "Internal processing error", "details": str(e)}

    def calculate_crowd_level(self, passenger_count: int) -> str:
        """
        Calculate crowd level based on passenger count

        Args:
            passenger_count: Number of passengers detected

        Returns:
            String representing the crowd level
        """
        try:
            for level, (min_count, max_count) in CROWD_THRESHOLDS.items():
                if min_count <= passenger_count <= max_count:
                    logger.debug(
                        f"Calculated crowd level {level} for {passenger_count} passengers"
                    )
                    return level
            return CrowdLevel.FULL
        except Exception as e:
            logger.error(f"Error calculating crowd level: {str(e)}")
            return CrowdLevel.EMPTY  # Default to EMPTY on error

    async def update_car_crowd_level(
        self,
        train_car: TrainCar,
        image_data: bytes
    ) -> Dict[str, Any]:
        """
        Process image and update car crowd level

        Args:
            train_car: TrainCar instance to update
            image_data: Raw bytes of the image file

        Returns:
            Dict containing updated crowd information or error message
        """
        try:
            # Validate input
            if not train_car or not image_data:
                return {"error": "Invalid input parameters"}

            # Process image with AI service
            result = await self.process_image(image_data)

            if "error" in result:
                return result

            passenger_count = result["message"]

            # Validate passenger count
            if not isinstance(passenger_count, int) or passenger_count < 0:
                return {"error": "Invalid passenger count from AI service"}

            # Calculate and update crowd level
            crowd_level = self.calculate_crowd_level(passenger_count)

            # Update train car
            train_car.current_passengers = passenger_count
            train_car.crowd_level = crowd_level
            train_car.save()

            response = {
                "success": True,
                "crowd_level": crowd_level,
                "passenger_count": passenger_count,
                "car_number": train_car.car_number,
                "train_number": train_car.train.train_number,
                "timestamp": train_car.last_updated.isoformat()
            }

            logger.info(f"Successfully updated crowd level: {response}")
            return response

        except Exception as e:
            error_msg = f"Error updating crowd level: {str(e)}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": error_msg
            }
