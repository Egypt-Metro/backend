# apps/trains/models/train.py

from decimal import Decimal
from typing import Optional
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils import timezone

from ..constants import (
    CARS_PER_TRAIN,
    DIRECTION_CHOICES,
    LINE_CONFIG,
    PEAK_HOURS,
    TRAIN_STATUS_CHOICES,
    TRAIN_TYPES,
    AVERAGE_SPEEDS
)


class Train(models.Model):
    """
    Model representing a metro train with real-time tracking capabilities.

    This model handles:
    - Train identification and basic properties
    - Location tracking
    - Status management
    - Schedule coordination
    - Capacity and crowd management
    """

    # Basic Information
    train_id = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        help_text="Unique identifier (format: line_number + train_number)"
    )

    line = models.ForeignKey(
        "stations.Line",
        on_delete=models.CASCADE,
        related_name='trains',
        help_text="Metro line this train operates on"
    )

    # Physical Properties
    number_of_cars = models.IntegerField(
        default=CARS_PER_TRAIN,
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        help_text="Number of cars in this train"
    )

    has_air_conditioning = models.BooleanField(
        default=False,
        help_text="Whether the train has air conditioning"
    )

    train_type = models.CharField(
        max_length=10,
        choices=TRAIN_TYPES,
        default="NON_AC",
        help_text="Type of train (AC/Non-AC)"
    )

    # Location Information
    current_station = models.ForeignKey(
        "stations.Station",
        on_delete=models.SET_NULL,
        null=True,
        related_name="current_trains",
        help_text="Current station where the train is located"
    )

    next_station = models.ForeignKey(
        "stations.Station",
        on_delete=models.SET_NULL,
        null=True,
        related_name="incoming_trains",
        help_text="Next station the train is heading to"
    )

    latitude = models.DecimalField(
        max_digits=8,
        decimal_places=6,
        default=Decimal('0.000000'),
        validators=[
            MinValueValidator(Decimal('-90.000000')),
            MaxValueValidator(Decimal('90.000000'))
        ],
        help_text="Current latitude of the train"
    )

    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        default=Decimal('0.000000'),
        validators=[
            MinValueValidator(Decimal('-180.000000')),
            MaxValueValidator(Decimal('180.000000'))
        ],
        help_text="Current longitude of the train"
    )

    # Operational Status
    direction = models.CharField(
        max_length=20,
        choices=DIRECTION_CHOICES,
        help_text="Current direction of travel"
    )

    status = models.CharField(
        max_length=20,
        choices=TRAIN_STATUS_CHOICES,
        default="IN_SERVICE",
        help_text="Current operational status"
    )

    speed = models.FloatField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(120)],
        help_text="Current speed in km/h"
    )

    # Timestamps
    last_updated = models.DateTimeField(
        auto_now=True,
        help_text="Last time train information was updated"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        null=True,
        blank=True,
        help_text="When this train was added to the system"
    )

    class Meta:
        indexes = [
            models.Index(fields=["train_id"]),
            models.Index(fields=["line", "status"]),
            models.Index(fields=["current_station"]),
            models.Index(fields=["direction", "status"]),
        ]
        ordering = ['line', 'train_id']
        verbose_name = "Metro Train"
        verbose_name_plural = "Metro Trains"

    def __str__(self):
        return (
            f"Train {self.train_id} - {self.line.name} "
            f"({'AC' if self.has_air_conditioning else 'Non-AC'}) "
            f"at {self.current_station.name if self.current_station else 'Unknown'}"
        )

    def clean(self):
        """Validate train data before saving."""
        if self.line_id:
            self._validate_line_config()
            self._validate_speed()
            self._validate_coordinates()

    def _validate_line_config(self):
        """Validate train against line configuration."""
        line_name = f"LINE_{self.line.name.replace(' ', '_')}"
        line_config = LINE_CONFIG.get(line_name)

        if line_config:
            # Validate AC requirement
            if line_config["has_ac_percentage"] == 100 and not self.has_air_conditioning:
                raise ValidationError(f"All trains on {self.line.name} must have air conditioning")

            # Validate direction
            valid_directions = [d[0] for d in line_config["directions"]]
            if self.direction and self.direction not in valid_directions:
                raise ValidationError(
                    f"Invalid direction for {self.line.name}. Valid choices: {', '.join(valid_directions)}"
                )

    def _validate_speed(self):
        """Validate train speed."""
        if self.speed < 0:
            raise ValidationError("Speed cannot be negative")

        line_config = LINE_CONFIG.get(f"LINE_{self.line.name.replace(' ', '_')}")
        if line_config and self.speed > line_config["speed_limit"]:
            raise ValidationError(f"Speed exceeds line limit of {line_config['speed_limit']} km/h")

    def _validate_coordinates(self):
        """Validate geographic coordinates."""
        if abs(self.latitude) > 90:
            raise ValidationError("Latitude must be between -90 and 90 degrees")
        if abs(self.longitude) > 180:
            raise ValidationError("Longitude must be between -180 and 180 degrees")

    def save(self, *args, **kwargs):
        """Override save to ensure data consistency."""
        # Update train type based on AC status
        self.train_type = "AC" if self.has_air_conditioning else "NON_AC"

        # Ensure coordinates have proper precision
        self.latitude = Decimal(str(round(float(self.latitude), 6)))
        self.longitude = Decimal(str(round(float(self.longitude), 6)))

        self.full_clean()
        super().save(*args, **kwargs)

    # Utility methods
    def get_next_station_arrival(self) -> Optional[timezone.datetime]:
        """Calculate estimated arrival time at next station."""
        if not all([self.current_station, self.next_station, self.speed > 0]):
            return None

        distance = self.current_station.distance_to(self.next_station)
        time_in_hours = distance / (self.speed * 1000)  # Convert speed to m/h
        return timezone.now() + timezone.timedelta(hours=time_in_hours)

    def is_delayed(self) -> bool:
        """Check if train is delayed."""
        return self.status == "DELAYED"

    def is_peak_hour(self) -> bool:
        """Check if current time is during peak hours."""
        current_time = timezone.now().time()

        for period, times in PEAK_HOURS.items():
            start = timezone.datetime.strptime(times["start"], "%H:%M").time()
            end = timezone.datetime.strptime(times["end"], "%H:%M").time()
            if start <= current_time <= end:
                return True
        return False

    def get_current_speed(self) -> float:
        """Get appropriate speed based on current conditions."""
        base_speed = AVERAGE_SPEEDS["PEAK" if self.is_peak_hour() else "NORMAL"]
        return min(base_speed, self.speed)

    @property
    def formatted_id(self) -> str:
        """Return a formatted version of the train ID."""
        return f"{self.get_line_number()}-{self.get_train_number():03d}"

    def get_train_number(self) -> int:
        """Extract the train number from train_id."""
        return int(str(self.train_id)[-3:])

    def get_line_number(self) -> int:
        """Extract the line number from train_id."""
        return int(str(self.train_id)[:-3])
