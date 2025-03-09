# apps/trains/constants/choices.py

from django.db import models

CARS_PER_TRAIN = 10
MAX_SCHEDULES = 3


class TrainStatus(models.TextChoices):
    IN_SERVICE = 'IN_SERVICE', 'In Service'
    DELAYED = 'DELAYED', 'Delayed'
    MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'
    OUT_OF_SERVICE = 'OUT_OF_SERVICE', 'Out of Service'


class CrowdLevel(models.TextChoices):
    EMPTY = 'EMPTY', 'Empty'
    LOW = 'LOW', 'Low'
    MEDIUM = 'MEDIUM', 'Medium'
    HIGH = 'HIGH', 'High'
    FULL = 'FULL', 'Full'


CROWD_THRESHOLDS = {
    CrowdLevel.EMPTY: (0, 0),
    CrowdLevel.LOW: (1, 10),
    CrowdLevel.MEDIUM: (11, 20),
    CrowdLevel.HIGH: (21, 29),
    CrowdLevel.FULL: (30, float('inf'))
}


class Direction(models.TextChoices):
    HELWAN = 'HELWAN', 'Helwan'
    MARG = 'MARG', 'El-Marg'
    SHOBRA = 'SHOBRA', 'Shobra El Kheima'
    MONIB = 'MONIB', 'El-Monib'
    ADLY = 'ADLY', 'Adly Mansour'
    KIT_KAT = 'KIT_KAT', 'Kit Kat'
