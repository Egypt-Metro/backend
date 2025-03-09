# apps/trains/models/train.py

from django.db import models
from django.core.exceptions import ValidationError
from ..constants.choices import CrowdLevel, TrainStatus, Direction, CARS_PER_TRAIN
from apps.stations.models import Station, Line


class Train(models.Model):
    train_number = models.CharField(max_length=50, unique=True)
    line = models.ForeignKey(Line, on_delete=models.CASCADE, related_name='trains')
    status = models.CharField(
        max_length=20,
        choices=TrainStatus.choices,
        default=TrainStatus.IN_SERVICE
    )
    has_ac = models.BooleanField(default=False)
    direction = models.CharField(
        max_length=20,
        choices=Direction.choices
    )
    current_station = models.ForeignKey(
        Station,
        on_delete=models.SET_NULL,
        null=True,
        related_name='current_trains'
    )
    next_station = models.ForeignKey(
        Station,
        on_delete=models.SET_NULL,
        null=True,
        related_name='upcoming_trains'
    )
    camera_car_number = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['train_number']),
            models.Index(fields=['line', 'status']),
            models.Index(fields=['current_station']),
        ]

    def __str__(self):
        return f"Train {self.train_number} - {self.line.name}"

    def clean(self):
        if self.camera_car_number and (self.camera_car_number < 1 or self.camera_car_number > CARS_PER_TRAIN):
            raise ValidationError(f"Camera car number must be between 1 and {CARS_PER_TRAIN}")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_monitored(self):
        return self.camera_car_number is not None

    def get_crowd_level(self):
        """Get crowd level for the monitored car"""
        if not self.is_monitored:
            return None
        try:
            car = self.cars.get(car_number=self.camera_car_number)
            return car.crowd_level
        except TrainCar.DoesNotExist:
            return None


class TrainCar(models.Model):
    train = models.ForeignKey(Train, on_delete=models.CASCADE, related_name='cars')
    car_number = models.PositiveIntegerField()
    has_camera = models.BooleanField(default=False)
    current_passengers = models.PositiveIntegerField(default=0)
    crowd_level = models.CharField(
        max_length=20,
        choices=CrowdLevel.choices,
        default=CrowdLevel.EMPTY
    )
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('train', 'car_number')
        ordering = ['car_number']

    def __str__(self):
        return f"Car {self.car_number} of Train {self.train.train_number}"
