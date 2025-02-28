# apps/trains/services/schedule_service.py

from typing import List, Dict, Optional
from datetime import timedelta
import random
import logging
from django.utils import timezone
from django.core.cache import cache
from django.db.models import QuerySet

from ..models import Schedule, Train
from ..constants import (
    SCHEDULE_TIME_WINDOW,
    MAX_SCHEDULES,
    ScheduleStatus,
)

logger = logging.getLogger(__name__)


class ScheduleService:
    """Service for managing train schedules and retrieving upcoming trains."""

    CACHE_TIMEOUT = 60  # 1 minute cache

    @classmethod
    def get_upcoming_trains_for_station(
        cls,
        station_id: int,
        limit: int = 3,
        use_cache: bool = True
    ) -> List[Dict]:
        """
        Get upcoming trains for a station with detailed information.

        Args:
            station_id: ID of the station
            limit: Number of upcoming trains to return
            use_cache: Whether to use cached data

        Returns:
            List of upcoming train schedules with details
        """
        try:
            cache_key = f"upcoming_trains_station_{station_id}"

            if use_cache:
                cached_data = cache.get(cache_key)
                if cached_data:
                    return cached_data

            current_time = timezone.now()

            # Get upcoming schedules with optimized queries
            schedules = Schedule.objects.filter(
                station_id=station_id,
                arrival_time__gte=current_time,
                is_active=True,
                train__status='IN_SERVICE'  # Only get active trains
            ).select_related(
                'train',
                'train__line',
                'station',
                'train__current_station',
                'train__next_station'
            ).prefetch_related(
                'train__cars'
            ).order_by('arrival_time')[:limit]

            upcoming_trains = []
            for schedule in schedules:
                train_info = cls._build_train_info(schedule)
                upcoming_trains.append(train_info)

            if use_cache and upcoming_trains:
                cache.set(cache_key, upcoming_trains, cls.CACHE_TIMEOUT)

            return upcoming_trains

        except Exception as e:
            logger.error(f"Error getting upcoming trains for station {station_id}: {str(e)}")
            return []

    @classmethod
    def _build_train_info(cls, schedule: Schedule) -> Dict:
        """Build detailed train information dictionary."""
        try:
            train = schedule.train
            car_info = cls._get_car_info(train)
            delay_minutes = cls._calculate_delay(schedule)

            return {
                "schedule_id": schedule.id,
                "train": {
                    "id": train.id,
                    "train_number": train.train_id,
                    "line": {
                        "name": train.line.name,
                        "color": train.line.color_code
                    },
                    "status": train.status,
                    "direction": train.direction,
                    "has_ac": train.has_air_conditioning,
                    "current_station": train.current_station.name,
                    "next_station": train.next_station.name,
                    "cars": car_info
                },
                "timing": {
                    "scheduled_arrival": schedule.arrival_time,
                    "estimated_arrival": schedule.arrival_time + timedelta(minutes=delay_minutes),
                    "delay_minutes": delay_minutes
                },
                "crowd_info": {
                    "overall_level": schedule.expected_crowd_level,
                    "car_details": car_info
                },
                "service_info": cls._get_service_info(train, delay_minutes)
            }
        except Exception as e:
            logger.error(f"Error building train info for schedule {schedule.id}: {str(e)}")
            return {}

    @staticmethod
    def _get_car_info(train: Train) -> List[Dict]:
        """Get information about train cars."""
        try:
            return [
                {
                    "car_number": car.car_number,
                    "crowd_level": car.crowd_status,
                    "available_seats": max(0, car.capacity - car.current_load),
                    "temperature": random.randint(20, 25) if train.has_air_conditioning else None
                }
                for car in train.cars.all()
            ]
        except Exception as e:
            logger.error(f"Error getting car info for train {train.id}: {str(e)}")
            return []

    @staticmethod
    def _calculate_delay(schedule: Schedule) -> int:
        """Calculate delay for a schedule."""
        try:
            if schedule.status == ScheduleStatus.DELAYED:
                return random.randint(5, 15)  # Simulated delay
            return 0
        except Exception:
            return 0

    @staticmethod
    def _get_service_info(train: Train, delay_minutes: int) -> Dict:
        """Get service information for a train."""
        try:
            service_info = {
                "is_operational": train.status == "IN_SERVICE",
                "amenities": [],
                "announcements": []
            }

            if train.has_air_conditioning:
                service_info["amenities"] = [
                    "WiFi",
                    "USB Charging",
                    "Air Conditioning"
                ]

            if delay_minutes > 0:
                service_info["announcements"].append(
                    f"Train delayed by {delay_minutes} minutes"
                )

            return service_info
        except Exception as e:
            logger.error(f"Error getting service info for train {train.id}: {str(e)}")
            return {"is_operational": False, "amenities": [], "announcements": []}

    @classmethod
    def get_upcoming_schedules(
        cls,
        station_id: int,
        time_window: int = SCHEDULE_TIME_WINDOW
    ) -> QuerySet:
        """Get upcoming schedules for a station."""
        try:
            current_time = timezone.now()
            end_time = current_time + timedelta(minutes=time_window)

            return Schedule.objects.filter(
                station_id=station_id,
                arrival_time__gte=current_time,
                arrival_time__lte=end_time,
                is_active=True
            ).select_related(
                "train",
                "train__line",
                "station"
            ).order_by("arrival_time")[:MAX_SCHEDULES]
        except Exception as e:
            logger.error(f"Error getting upcoming schedules: {str(e)}")
            return Schedule.objects.none()

    @classmethod
    def update_schedule(
        cls,
        schedule_id: int,
        new_status: Optional[str] = None,
        new_arrival_time: Optional[timezone.datetime] = None
    ) -> Optional[Schedule]:
        """Update schedule status and/or arrival time."""
        try:
            schedule = Schedule.objects.get(id=schedule_id)
            if new_status:
                schedule.update_status(new_status, new_arrival_time)
            return schedule
        except Schedule.DoesNotExist:
            logger.error(f"Schedule {schedule_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error updating schedule {schedule_id}: {str(e)}")
            return None

    @classmethod
    def cancel_schedule(cls, schedule_id: int) -> Optional[Schedule]:
        """Cancel a schedule."""
        try:
            schedule = Schedule.objects.get(id=schedule_id)
            schedule.update_status(ScheduleStatus.CANCELLED)
            schedule.is_active = False
            schedule.save()
            return schedule
        except Schedule.DoesNotExist:
            logger.error(f"Schedule {schedule_id} not found")
            return None
        except Exception as e:
            logger.error(f"Error cancelling schedule {schedule_id}: {str(e)}")
            return None
