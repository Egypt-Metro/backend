# apps/trains/services/crowd_service.py
import logging
import io
from PIL import Image
from typing import Dict, Any, Optional

from django.utils import timezone
from django.db.models import Avg
from django.db import transaction
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
        Initialize CrowdDetectionService with AI service and configuration
        """
        self.ai_service = AIService()
        self.max_file_size = settings.AI_SERVICE_CONFIG['MAX_FILE_SIZE']
        self.allowed_extensions = settings.AI_SERVICE_CONFIG['ALLOWED_EXTENSIONS']

    async def validate_image(self, image_data: bytes) -> bool:
        """
        Comprehensive asynchronous image validation

        Args:
            image_data (bytes): Raw image data to validate

        Returns:
            bool: Whether the image is valid
        """
        try:
            # Validate file size
            if len(image_data) > self.max_file_size:
                logger.warning(f"Image exceeds max size of {self.max_file_size} bytes")
                return False

            # Validate image using Pillow
            with Image.open(io.BytesIO(image_data)) as img:
                # Check file format
                file_format = img.format.lower() if img.format else None
                format_mapping = {
                    'jpeg': 'jpg',
                    'png': 'png',
                    'jpg': 'jpg'
                }

                detected_format = format_mapping.get(file_format)

                # Validate file type and dimensions
                if (
                    not detected_format
                    or detected_format not in self.allowed_extensions
                    or img.width == 0
                    or img.height == 0
                ):
                    logger.warning(f"Invalid image: format={file_format}, dimensions={img.size}")
                    return False

            return True
        except Exception as e:
            logger.error(f"Image validation error: {e}", exc_info=True)
            return False

    def calculate_crowd_level(self, passenger_count: int) -> str:
        """
        Determine crowd level based on passenger count

        Args:
            passenger_count (int): Number of passengers

        Returns:
            str: Crowd level classification
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
        Comprehensive method to update train car crowd level with robust error handling

        Args:
            train_car (TrainCar): Train car to update
            image_data (bytes): Image data for crowd detection

        Returns:
            Dict with crowd detection results
        """
        # Comprehensive input validation
        if not train_car:
            return {
                "success": False,
                "error": "Invalid train car",
                "details": "Train car object is None or invalid"
            }

        if not image_data:
            return {
                "success": False,
                "error": "No image provided",
                "details": "Image data is empty or missing"
            }

        try:
            # Validate image asynchronously
            if not await self.validate_image(image_data):
                return {
                    "success": False,
                    "error": "Invalid image",
                    "details": "Image failed validation checks",
                    "suggestions": [
                        "Ensure image is not corrupted",
                        f"Max file size is {self.max_file_size / (1024 * 1024)} MB",
                        f"Allowed types: {', '.join(self.allowed_extensions)}"
                    ]
                }

            # Process image via AI service with comprehensive error handling
            try:
                result = await self.ai_service.process_image(image_data)
            except Exception as ai_service_error:
                logger.error(f"AI Service processing error: {ai_service_error}", exc_info=True)
                return {
                    "success": False,
                    "error": "AI service processing failed",
                    "details": str(ai_service_error),
                    "fallback_suggestion": [
                        "Check AI service availability",
                        "Verify network connectivity",
                        "Retry the request",
                        "Contact system administrator"
                    ]
                }

            # Validate AI service response
            if "error" in result:
                logger.error(f"AI Service Error: {result}")
                return {
                    "success": False,
                    "error": "AI service processing failed",
                    "details": result.get('error', 'Unknown error'),
                    "fallback_suggestion": [
                        "Verify AI service status",
                        "Check network connectivity",
                        "Retry the request"
                    ]
                }

            # Extract and validate passenger count
            passenger_count = result.get("message", 0)
            if not isinstance(passenger_count, int) or passenger_count < 0:
                return {
                    "success": False,
                    "error": "Invalid passenger count",
                    "details": f"Received: {passenger_count}",
                    "suggestions": [
                        "Verify AI service output",
                        "Check image quality",
                        "Retry with a different image"
                    ]
                }

            # Calculate crowd level
            crowd_level = self.calculate_crowd_level(passenger_count)

            # Use database transaction for atomic update
            try:
                with transaction.atomic():
                    train_car.current_passengers = passenger_count
                    train_car.crowd_level = crowd_level
                    train_car.last_updated = timezone.now()
                    train_car.save(
                        update_fields=[
                            'current_passengers',
                            'crowd_level',
                            'last_updated'
                        ]
                    )
            except Exception as db_error:
                logger.error(f"Database update error: {db_error}", exc_info=True)
                return {
                    "success": False,
                    "error": "Database update failed",
                    "details": str(db_error),
                    "fallback_suggestion": [
                        "Check database connection",
                        "Verify data integrity",
                        "Retry the request"
                    ]
                }

            # Prepare successful response
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

        except Exception as unexpected_error:
            # Catch-all for any unexpected errors
            logger.error(
                f"Unexpected error in crowd detection: {unexpected_error}",
                exc_info=True
            )
            return {
                "success": False,
                "error": "Comprehensive detection failure",
                "details": str(unexpected_error),
                "fallback_suggestion": [
                    "Check system logs",
                    "Verify AI service status",
                    "Contact system administrator",
                    "Retry the request"
                ]
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
