from asgiref.sync import sync_to_async
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from typing import Dict, Any
import logging

from ..models.train import TrainCar
from ..constants.choices import CrowdLevel, CROWD_THRESHOLDS
from .ai_service import AIService

logger = logging.getLogger(__name__)


class CrowdDetectionService:
    def __init__(self):
        self.ai_service = AIService()
        self.max_file_size = settings.AI_SERVICE_CONFIG['MAX_FILE_SIZE']
        self.allowed_extensions = settings.AI_SERVICE_CONFIG['ALLOWED_EXTENSIONS']

    @sync_to_async
    def _update_train_car(self, train_car: TrainCar, passenger_count: int, crowd_level: str) -> bool:
        """Update train car data in a sync context"""
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
            return True
        except Exception as e:
            logger.error(f"Database update error: {e}", exc_info=True)
            return False

    def calculate_crowd_level(self, passenger_count: int) -> str:
        """Calculate crowd level from passenger count"""
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
        """Process image and update crowd level with proper async/sync handling"""
        start_time = timezone.now()

        # Input validation
        if not train_car or not image_data:
            return {
                "success": False,
                "error": "Invalid input",
                "details": "Train car or image data is missing"
            }

        try:
            # Process image with AI service
            result = await self.ai_service.process_image(image_data)

            if not result.get("success", False):
                logger.error(f"AI service error: {result.get('error')}")
                return {
                    "success": False,
                    "error": "AI service processing failed",
                    "details": result.get("error", "Unknown error"),
                    "suggestions": result.get("suggestions", [
                        "Verify AI service status",
                        "Check network connectivity",
                        "Retry the request"
                    ])
                }

            # Extract and validate passenger count
            passenger_count = result.get("message", 0)
            if not isinstance(passenger_count, int) or passenger_count < 0:
                return {
                    "success": False,
                    "error": "Invalid passenger count",
                    "details": f"Received: {passenger_count}"
                }

            # Calculate crowd level
            crowd_level = self.calculate_crowd_level(passenger_count)

            # Update database
            update_success = await self._update_train_car(train_car, passenger_count, crowd_level)
            if not update_success:
                return {
                    "success": False,
                    "error": "Database update failed",
                    "details": "Failed to save crowd level information"
                }

            # Return successful response
            processing_time = (timezone.now() - start_time).total_seconds()
            return {
                "success": True,
                "crowd_level": crowd_level,
                "passenger_count": passenger_count,
                "car_number": train_car.car_number,
                "train_number": train_car.train.train_number,
                "timestamp": timezone.now().isoformat(),
                "processing_time": f"{processing_time:.2f} seconds"
            }

        except Exception as e:
            logger.error(f"Unexpected error in crowd detection: {e}", exc_info=True)
            return {
                "success": False,
                "error": "Processing failed",
                "details": str(e),
                "suggestions": [
                    "Check system logs",
                    "Verify AI service status",
                    "Retry the request"
                ]
            }
