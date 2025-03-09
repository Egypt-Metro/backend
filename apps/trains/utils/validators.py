# apps/trains/utils/validators.py

from django.core.exceptions import ValidationError
from datetime import datetime, timedelta


def validate_train_number(train_number: str):
    """Validate train number format"""
    if not train_number or len(train_number) < 4:
        raise ValidationError("Train number must be at least 4 characters")
    if not train_number.startswith(('T', 'M')):
        raise ValidationError("Train number must start with T or M")


def validate_schedule_times(arrival_time: datetime, departure_time: datetime):
    """Validate schedule times"""
    if departure_time <= arrival_time:
        raise ValidationError("Departure time must be after arrival time")

    if (departure_time - arrival_time) > timedelta(minutes=10):
        raise ValidationError("Stop time cannot exceed 10 minutes")


def validate_car_number(car_number: int, max_cars: int = 10):
    """Validate car number"""
    if not isinstance(car_number, int) or car_number < 1 or car_number > max_cars:
        raise ValidationError(f"Car number must be between 1 and {max_cars}")
