# apps/trains/services/crowd_service.py

import logging

from django.core.cache import cache
from django.db.models import Avg
from django.utils import timezone

from apps.trains.constants import CARS_PER_TRAIN

from ..models import CrowdMeasurement, TrainCar

logger = logging.getLogger(__name__)


class CrowdService:
    CACHE_TIMEOUT = 300  # 5 minutes

    @staticmethod
    def update_crowd_level(train_car_id, passenger_count, method="AI_CAMERA", confidence=0.95):
        """Update crowd level for a train car"""
        try:
            train_car = TrainCar.objects.get(id=train_car_id)

            # Create crowd measurement
            measurement = CrowdMeasurement.objects.create(
                train_car=train_car,
                passenger_count=passenger_count,
                crowd_percentage=(passenger_count / train_car.capacity) * 100,
                confidence_score=confidence,
                measurement_method=method,
            )

            # Update train car current load
            train_car.current_load = passenger_count
            train_car.save()

            # Clear cache
            cache.delete(f"crowd_level_{train_car_id}")

            return measurement
        except Exception as e:
            logger.error(f"Error updating crowd level: {e}")
            raise

    def get_crowd_levels(self, train):
        """Get current crowd levels for all cars in a train"""
        try:
            # Get all cars ordered by number
            cars = train.cars.all().order_by('car_number')
            crowd_data = []

            # Ensure we have data for all 10 cars
            for car_number in range(1, CARS_PER_TRAIN + 1):
                car = next((c for c in cars if c.car_number == car_number), None)

                if car:
                    crowd_data.append({
                        "car_id": car.car_number,
                        "crowd_level": car.load_percentage / 100,
                        "timestamp": car.last_updated.isoformat()
                    })
                else:
                    # Add default data for missing cars
                    crowd_data.append({
                        "car_id": car_number,
                        "crowd_level": 0.0,
                        "timestamp": timezone.now().isoformat()
                    })

            return {
                "train_id": train.id,
                "crowd_data": crowd_data,
                "is_ac": train.has_air_conditioning
            }
        except Exception as e:
            logger.error(f"Error getting crowd levels: {e}")
            return None

    @staticmethod
    def get_crowd_history(train_car_id, hours=24):
        """Get crowd level history for a train car"""
        time_threshold = timezone.now() - timezone.timedelta(hours=hours)

        return CrowdMeasurement.objects.filter(train_car_id=train_car_id, timestamp__gte=time_threshold).order_by(
            "timestamp"
        )

    @staticmethod
    def get_line_crowding(line_id):
        """Get crowding information for an entire line"""
        return TrainCar.objects.filter(train__line_id=line_id).aggregate(
            avg_load=Avg("current_load"), avg_percentage=Avg("current_load") * 100 / Avg("capacity")
        )

    @staticmethod
    def predict_crowding(train_car_id, timestamp):
        """Predict crowd levels for a specific time"""
        # Get historical data for the same day/time
        day_of_week = timestamp.weekday()
        time_of_day = timestamp.time()

        historical_data = CrowdMeasurement.objects.filter(
            train_car_id=train_car_id, timestamp__week_day=day_of_week, timestamp__time__hour=time_of_day.hour
        ).aggregate(Avg("passenger_count"))

        return historical_data["passenger_count__avg"] or 0
