# apps/trains/models/crowd.py

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from ..constants import CAR_CAPACITY, CROWD_LEVELS


class TrainCar(models.Model):
    train = models.ForeignKey("Train", on_delete=models.CASCADE, related_name="cars")
    car_number = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    capacity = models.IntegerField(default=CAR_CAPACITY["TOTAL"])
    current_load = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    is_operational = models.BooleanField(default=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("train", "car_number")
        ordering = ["car_number"]
        indexes = [
            models.Index(fields=["train", "car_number"]),
            models.Index(fields=["is_operational"]),
        ]

    def __str__(self):
        return f"{self.train.train_id} - Car {self.car_number}"

    def clean(self):
        if self.current_load > self.capacity:
            raise ValidationError("Current load cannot exceed capacity")
        if self.current_load < 0:
            raise ValidationError("Current load cannot be negative")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

        # Create crowd measurement record
        CrowdMeasurement.objects.create(
            train_car=self,
            passenger_count=self.current_load,
            crowd_percentage=self.load_percentage,
            confidence_score=0.95,  # Default high confidence for direct measurements
            measurement_method="WEIGHT_SENSOR",
        )

    @property
    def load_percentage(self):
        """Calculate the current load percentage"""
        if self.capacity:
            percentage = (self.current_load / self.capacity) * 100
            return round(percentage, 2)  # Round to 2 decimal places
        return 0

    @property
    def crowd_status(self):
        """Determine crowd status based on load percentage"""
        percentage = self.load_percentage
        for status, (min_val, max_val) in CROWD_LEVELS.items():
            if min_val <= percentage <= max_val:
                return status
        return "UNKNOWN"

    def update_load(self, count, method="WEIGHT_SENSOR", confidence=0.95):
        """Update passenger count with measurement tracking"""
        if count > self.capacity:
            raise ValidationError(f"Count {count} exceeds car capacity {self.capacity}")

        self.current_load = count
        self.last_updated = timezone.now()
        self.save()

        return CrowdMeasurement.objects.create(
            train_car=self,
            passenger_count=count,
            crowd_percentage=self.load_percentage,
            confidence_score=confidence,
            measurement_method=method,
        )


class CrowdMeasurement(models.Model):
    """Track crowd measurements over time with different methods"""

    MEASUREMENT_METHODS = [
        ("AI_CAMERA", "AI Camera Detection"),
        ("WEIGHT_SENSOR", "Weight Sensor"),
        ("MANUAL", "Manual Count"),
        ("ESTIMATED", "AI Estimated"),
    ]

    train_car = models.ForeignKey(TrainCar, on_delete=models.CASCADE, related_name="measurements")
    timestamp = models.DateTimeField(auto_now_add=True)
    passenger_count = models.IntegerField()
    crowd_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,  # Store only 2 decimal places
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    confidence_score = models.DecimalField(
        max_digits=3,
        decimal_places=2,  # Store only 2 decimal places
        validators=[MinValueValidator(0), MaxValueValidator(1)],
        help_text="Confidence level of the measurement (0-1)",
    )
    measurement_method = models.CharField(
        max_length=20, choices=MEASUREMENT_METHODS, help_text="Method used to measure crowd levels"
    )

    class Meta:
        indexes = [
            models.Index(fields=["timestamp"]),
            models.Index(fields=["train_car", "timestamp"]),
            models.Index(fields=["measurement_method"]),
        ]
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.train_car} - {self.passenger_count} passengers ({self.measurement_method})"

    @property
    def is_reliable(self):
        """Check if measurement is considered reliable"""
        return self.confidence_score >= 0.8

    @property
    def formatted_crowd_percentage(self):
        return round(self.crowd_percentage, 2)

    @classmethod
    def get_recent_measurements(cls, train_car, minutes=15):
        """Get recent measurements for a train car"""
        time_threshold = timezone.now() - timezone.timedelta(minutes=minutes)
        return cls.objects.filter(train_car=train_car, timestamp__gte=time_threshold).order_by("-timestamp")
