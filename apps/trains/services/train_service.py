# apps/trains/services/train_service.py

import logging
from os import name

from django.core.cache import cache
from django.db.models import Count, Q
from django.utils import timezone

from apps.stations.models import Line

from ..constants import CROWD_LEVELS, LINE_CONFIG, PEAK_HOURS
from ..models import Train, TrainCar

logger = logging.getLogger(name)


class TrainService:
    CACHE_TIMEOUT = 300  # 5 minutes


def get_train_status(self, train_id):
    """Get comprehensive train status with caching"""
    cache_key = f"train_status_{train_id}"
    status = cache.get(cache_key)

    if not status:
        try:
            train = Train.objects.select_related("line", "current_station", "next_station").get(train_id=train_id)

            status = {
                "train_id": train.train_id,
                "line": train.line.name,
                "current_station": {
                    "name": (train.current_station.name if train.current_station else None),
                    "arrival_time": self._format_time(train.get_next_station_arrival()),
                },
                "next_station": {
                    "name": train.next_station.name if train.next_station else None,
                    "estimated_arrival": self._format_time(train.get_next_station_arrival()),
                },
                "status": train.status,
                "direction": train.direction,
                "has_ac": train.has_air_conditioning,
                "speed": train.speed,
                "location": {
                    "latitude": float(train.latitude) if train.latitude else None,
                    "longitude": float(train.longitude) if train.longitude else None,
                },
                "crowd_levels": self.get_crowd_levels(train),
                "is_peak_hour": train.is_peak_hour(),
                "last_updated": train.last_updated.isoformat(),
            }

            cache.set(cache_key, status, self.CACHE_TIMEOUT)
        except Train.DoesNotExist:
            logger.warning(f"Train not found: {train_id}")
            return None
        except Exception as e:
            logger.error(f"Error getting train status: {e}")
            return None

    return status


def get_crowd_levels(self, train):
    """Get crowd levels for all cars"""
    cache_key = f"crowd_levels_{train.id}"
    crowd_levels = cache.get(cache_key)

    if not crowd_levels:
        try:
            cars = TrainCar.objects.filter(train=train)
            crowd_levels = [
                {
                    "car_number": car.car_number,
                    "capacity": car.capacity,
                    "current_load": car.current_load,
                    "crowd_percentage": (car.current_load / car.capacity) * 100,
                    "status": self._get_crowd_status(car.current_load, car.capacity),
                }
                for car in cars
            ]
            cache.set(cache_key, crowd_levels, self.CACHE_TIMEOUT)
        except Exception as e:
            logger.error(f"Error getting crowd levels: {e}")
            return []

    return crowd_levels


def update_train_location(self, train_id, station_id=None, latitude=None, longitude=None, speed=None):
    """Update train location and related data"""
    try:
        train = Train.objects.get(train_id=train_id)

        if station_id:
            train.current_station_id = station_id

        if latitude is not None and longitude is not None:
            train.latitude = latitude
            train.longitude = longitude

        if speed is not None:
            train.speed = speed

        train.last_updated = timezone.now()
        train.save()

        # Invalidate cache
        cache.delete(f"train_status_{train_id}")
        cache.delete(f"crowd_levels_{train.id}")

        return self.get_train_status(train_id)
    except Exception as e:
        logger.error(f"Error updating train location: {e}")
        return None


def validate_line_ac_distribution(self, line_id):
    """Validate AC distribution for a specific line"""
    try:
        line_stats = Train.objects.filter(line_id=line_id).aggregate(
            total_trains=Count("id"),
            ac_trains=Count("id", filter=Q(has_air_conditioning=True)),
        )

        line = Line.objects.get(id=line_id)
        line_name = f"LINE_{line.name}"
        config = LINE_CONFIG.get(line_name)

        if not config:
            return True

        required_ac_trains = int((config["has_ac_percentage"] / 100) * line_stats["total_trains"])

        return line_stats["ac_trains"] == required_ac_trains
    except Exception as e:
        logger.error(f"Error validating AC distribution: {e}")
        return False


def get_line_trains(self, line_id):
    """Get all trains for a specific line"""
    cache_key = f"line_trains_{line_id}"
    trains_data = cache.get(cache_key)

    if not trains_data:
        try:
            trains = Train.objects.filter(line_id=line_id).select_related("line", "current_station", "next_station")
            trains_data = [self.get_train_status(train.train_id) for train in trains]
            cache.set(cache_key, trains_data, self.CACHE_TIMEOUT)
        except Exception as e:
            logger.error(f"Error getting line trains: {e}")
            return []

    return trains_data


def _get_crowd_status(self, current_load, capacity):
    """Determine crowd status based on load percentage"""
    percentage = (current_load / capacity) * 100
    for status, (min_val, max_val) in CROWD_LEVELS.items():
        if min_val <= percentage <= max_val:
            return status
    return "UNKNOWN"


def _format_time(self, dt):
    """Format datetime for API response"""
    return dt.isoformat() if dt else None


def is_peak_hour(self):
    """Check if current time is during peak hours"""
    current_time = timezone.now().time()

    for period, times in PEAK_HOURS.items():
        start = timezone.datetime.strptime(times["start"], "%H:%M").time()
        end = timezone.datetime.strptime(times["end"], "%H:%M").time()
        if start <= current_time <= end:
            return True

    return False
