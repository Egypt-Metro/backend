# apps/trains/services/crowd_service.py
import logging
from typing import Dict, Any, Optional

from django.utils import timezone
from django.db.models import Avg
from django.conf import settings

from ..models.train import TrainCar
from ..constants.choices import CrowdLevel, CROWD_THRESHOLDS
from .ai_service import AIService

logger = logging.getLogger(__name__)


class CrowdDetectionService:
    """
    Service for detecting and managing crowd levels in train cars

    Responsibilities:
    - Process images via AI service
    - Calculate crowd levels
    - Update train car crowd information
    """

    def __init__(self):
        """
        Initialize CrowdDetectionService with AI service
        """
        self.ai_service = AIService()
        self.max_file_size = settings.AI_SERVICE_CONFIG['MAX_FILE_SIZE']
        self.allowed_extensions = settings.AI_SERVICE_CONFIG['ALLOWED_EXTENSIONS']

    def validate_image(self, image_data: bytes) -> bool:
        """
        Validate image before processing

        Args:
            image_data (bytes): Raw image data

        Returns:
            bool: Whether image is valid
        """
        try:
            # Check file size
            if len(image_data) > self.max_file_size:
                logger.warning(f"Image exceeds max size of {self.max_file_size} bytes")
                return False

            # Additional validation can be added here
            return True
        except Exception as e:
            logger.error(f"Image validation error: {e}")
            return False

    def calculate_crowd_level(self, passenger_count: int) -> str:
        """
        Determine crowd level based on passenger count

        Args:
            passenger_count (int): Number of passengers

        Returns:
            str: Crowd level (e.g., EMPTY, MODERATE, CROWDED, FULL)
        """
        try:
            for level, (min_count, max_count) in CROWD_THRESHOLDS.items():
                if min_count <= passenger_count <= max_count:
                    return level
            return CrowdLevel.FULL
        except Exception as e:
            logger.error(f"Crowd level calculation error: {e}")
            return CrowdLevel.EMPTY

    async def update_car_crowd_level(
        self,
        train_car: TrainCar,
        image_data: bytes
    ) -> Dict[str, Any]:
        """
        Comprehensive method to update train car crowd level

        Args:
            train_car (TrainCar): Train car to update
            image_data (bytes): Image data for crowd detection

        Returns:
            Dict with crowd detection results
        """
        try:
            # Input validation
            if not train_car:
                return {"error": "Invalid train car", "success": False}

            if not image_data:
                return {"error": "No image provided", "success": False}

            # Image validation
            if not self.validate_image(image_data):
                return {
                    "error": "Invalid image",
                    "success": False,
                    "details": "Image failed validation checks"
                }

            # Process image via AI service
            result = await self.ai_service.process_image(image_data)

            # Check AI service response
            if "error" in result:
                logger.error(f"AI Service Error: {result}")
                return {
                    "success": False,
                    "error": "AI service processing failed",
                    "details": result.get('error', 'Unknown error')
                }

            # Extract passenger count
            passenger_count = result.get("message", 0)

            # Validate passenger count
            if not isinstance(passenger_count, int) or passenger_count < 0:
                return {
                    "success": False,
                    "error": "Invalid passenger count",
                    "details": f"Received: {passenger_count}"
                }

            # Calculate crowd level
            crowd_level = self.calculate_crowd_level(passenger_count)

            # Update train car details
            train_car.current_passengers = passenger_count
            train_car.crowd_level = crowd_level
            train_car.last_updated = timezone.now()
            train_car.save()

            # Prepare response
            response = {
                "success": True,
                "crowd_level": crowd_level,
                "passenger_count": passenger_count,
                "car_number": train_car.car_number,
                "train_number": train_car.train.train_number,
                "timestamp": train_car.last_updated.isoformat()
            }

            logger.info(f"Crowd level updated successfully: {response}")
            return response

        except Exception as e:
            error_msg = f"Unexpected error in crowd detection: {e}"
            logger.error(error_msg)
            return {
                "success": False,
                "error": "Unexpected error",
                "details": str(e)
            }

    def get_crowd_trend(self, train_car: TrainCar, hours: int = 24) -> Optional[Dict]:
        """
        Analyze crowd level trends for a train car

        Args:
            train_car (TrainCar): Train car to analyze
            hours (int): Hours of historical data to consider

        Returns:
            Dict with crowd trend information or None
        """
        try:
            # Calculate time threshold
            time_threshold = timezone.now() - timezone.timedelta(hours=hours)

            # Get historical crowd data
            historical_data = train_car.crowd_logs.filter(
                timestamp__gte=time_threshold
            ).order_by('timestamp')

            if not historical_data.exists():
                return None

            # Analyze trends
            trend_data = {
                'average_passengers': historical_data.aggregate(Avg('passenger_count'))['passenger_count__avg'],
                'peak_hours': self._find_peak_hours(historical_data),
                'trend_direction': self._determine_trend_direction(historical_data)
            }

            return trend_data

        except Exception as e:
            logger.error(f"Error analyzing crowd trend: {e}")
            return None

    def _find_peak_hours(self, historical_data):
        """
        Find peak crowd hours from historical data
        """
        # Implementation depends on your specific requirements
        pass

    def _determine_trend_direction(self, historical_data):
        """
        Determine crowd trend direction
        """
        # Implementation depends on your specific requirements
        pass
