from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import DecimalValidator
from django.db import models
from django.utils import timezone

from ..constants import CARS_PER_TRAIN, DIRECTION_CHOICES, LINE_CONFIG, PEAK_HOURS, TRAIN_STATUS_CHOICES, TRAIN_TYPES


class Train(models.Model):
    train_id = models.CharField(
        max_length=10,
        unique=True,
        db_index=True,
        help_text="Unique numeric identifier for the train"
    )
    line = models.ForeignKey("stations.Line", on_delete=models.CASCADE)
    number_of_cars = models.IntegerField(default=CARS_PER_TRAIN)
    has_air_conditioning = models.BooleanField(default=False)
    train_type = models.CharField(max_length=10, choices=TRAIN_TYPES, default="NON_AC")
    current_station = models.ForeignKey(
        "stations.Station", on_delete=models.SET_NULL, null=True, related_name="current_trains"
    )
    next_station = models.ForeignKey(
        "stations.Station", on_delete=models.SET_NULL, null=True, related_name="incoming_trains"
    )
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES)
    status = models.CharField(max_length=20, choices=TRAIN_STATUS_CHOICES, default="IN_SERVICE")
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[DecimalValidator(9, 6)],
        default=Decimal("0.000000"),  # Add default value
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        validators=[DecimalValidator(9, 6)],
        default=Decimal("0.000000"),  # Add default value
    )
    speed = models.FloatField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["train_id"]),
            models.Index(fields=["line", "status"]),
            models.Index(fields=["current_station"]),
        ]
        ordering = ['train_id']

    def __str__(self):
        station_info = f" at {self.current_station.name}" if self.current_station else ""
        ac_status = "AC" if self.has_air_conditioning else "Non-AC"
        return f"Train {self.train_id} - Line {self.line.name} ({ac_status}){station_info}"

    def clean(self):
        if self.line_id:
            line_name = f"LINE_{self.line.name}"
            line_config = LINE_CONFIG.get(line_name)

            if line_config:
                # Validate AC requirement
                if line_config["has_ac_percentage"] == 100 and not self.has_air_conditioning:
                    raise ValidationError(f"All trains on {self.line.name} must have air conditioning")

                # Validate direction
                valid_directions = [d[0] for d in line_config["directions"]]
                if self.direction and self.direction not in valid_directions:
                    raise ValidationError(
                        f"Invalid direction for {self.line.name}. " f"Valid choices are: {', '.join(valid_directions)}"
                    )

            # Validate speed
            if self.speed < 0:
                raise ValidationError("Speed cannot be negative")
            if line_config and self.speed > line_config["speed_limit"]:
                raise ValidationError(f"Speed exceeds line limit of {line_config['speed_limit']} km/h")

    def get_train_number(self):
        """Extract the train number from train_id"""
        return int(str(self.train_id)[-3:])

    def get_line_number(self):
        """Extract the line number from train_id"""
        return int(str(self.train_id)[:-3])

    def save(self, *args, **kwargs):
        # Update train_type based on AC status
        self.train_type = "AC" if self.has_air_conditioning else "NON_AC"
        self.full_clean()
        super().save(*args, **kwargs)

    def get_next_station_arrival(self):
        """Calculate estimated arrival time at next station"""
        if not (self.current_station and self.next_station and self.speed):
            return None

        distance = self.current_station.distance_to(self.next_station)
        time_in_hours = distance / (self.speed * 1000)  # Convert speed to m/h
        return timezone.now() + timezone.timedelta(hours=time_in_hours)

    def is_delayed(self):
        """Check if train is delayed"""
        return self.status == "DELAYED"

    def is_peak_hour(self):
        """Check if current time is during peak hours"""
        current_time = timezone.now().time()

        for period, times in PEAK_HOURS.items():
            start = timezone.datetime.strptime(times["start"], "%H:%M").time()
            end = timezone.datetime.strptime(times["end"], "%H:%M").time()
            if start <= current_time <= end:
                return True
        return False

    @property
    def formatted_id(self):
        """Return a formatted version of the train ID"""
        line_num = self.get_line_number()
        train_num = self.get_train_number()
        return f"{line_num}-{train_num:03d}"
