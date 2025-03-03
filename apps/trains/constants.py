# apps/trains/constants.py
from django.db import models

# Common settings
CARS_PER_TRAIN = 10
STATION_STOP_TIME = 120  # seconds
SCHEDULE_TIME_WINDOW = 120  # minutes
MAX_SCHEDULES = 10

# Line configurations with actual station counts
LINE_CONFIG = {
    "LINE_First_Line": {
        "has_ac_percentage": 50,
        "total_trains": 30,
        "speed_limit": 80,
        "station_stop_time": 120,
        "total_stations": 35,
        "color_code": "#FF0000",
        "directions": [
            ("HELWAN", "Helwan"),
            ("MARG", "El-Marg"),
        ],
    },
    "LINE_Second_Line": {
        "has_ac_percentage": 50,
        "total_trains": 20,
        "speed_limit": 80,
        "station_stop_time": 120,
        "total_stations": 20,
        "color_code": "#0000FF",
        "directions": [
            ("SHOBRA", "Shobra El Kheima"),
            ("MONIB", "El-Monib"),
        ],
    },
    "LINE_Third_Line": {
        "has_ac_percentage": 100,
        "total_trains": 25,
        "speed_limit": 100,
        "station_stop_time": 120,
        "total_stations": 34,
        "color_code": "#00FF00",
        "directions": [
            ("ADLY", "Adly Mansour"),
            ("KIT_KAT", "Kit Kat"),
        ],
    },
}

# Train status choices
TRAIN_STATUS_CHOICES = [
    ("IN_SERVICE", "In Service"),
    ("DELAYED", "Delayed"),
    ("MAINTENANCE", "Under Maintenance"),
    ("OUT_OF_SERVICE", "Out of Service"),
]

DIRECTION_CHOICES = [
    ("HELWAN", "Helwan"),
    ("MARG", "El-Marg"),
    ("SHOBRA", "Shobra El Kheima"),
    ("MONIB", "El-Monib"),
    ("ADLY", "Adly Mansour"),
    ("KIT_KAT", "Kit Kat"),
]

# Train types
TRAIN_TYPES = [("AC", "Air Conditioned"), ("NON_AC", "Non Air Conditioned")]

# Crowd levels with realistic thresholds
CROWD_LEVELS = {
    "EMPTY": (0, 20),
    "LIGHT": (21, 40),
    "MODERATE": (41, 60),
    "CROWDED": (61, 80),
    "PACKED": (81, 100),
}

# Car capacity based on actual metro cars
CAR_CAPACITY = {
    "SEATED": 40,
    "STANDING": 140,
    "TOTAL": 180,
    "CRUSH": 220,
}

# Time windows for peak hours
PEAK_HOURS = {
    "MORNING": {
        "start": "07:00",
        "end": "10:00",
    },
    "EVENING": {
        "start": "16:00",
        "end": "19:00",
    },
}


class ScheduleStatus(models.TextChoices):
    ON_TIME = 'ON_TIME', 'On Time'
    DELAYED = 'DELAYED', 'Delayed'
    CANCELLED = 'CANCELLED', 'Cancelled'


class CrowdLevel(models.TextChoices):
    LOW = 'LOW', 'Low'
    MODERATE = 'MODERATE', 'Moderate'
    HIGH = 'HIGH', 'High'


# Average speeds
AVERAGE_SPEEDS = {
    "NORMAL": 60,
    "PEAK": 45,
    "OFF_PEAK": 70,
}

# Station dwell times
DWELL_TIMES = {
    "NORMAL": 30,
    "INTERCHANGE": 45,
    "TERMINAL": 60,
    "PEAK_FACTOR": 1.5,
}
