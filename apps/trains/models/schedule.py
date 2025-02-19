# apps/trains/models/schedule.py

import datetime

from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Schedule(models.Model):
    DAY_TYPES = [
        ("WEEKDAY", "Weekday"),
        ("SATURDAY", "Saturday"),
        ("SUNDAY", "Sunday"),
        ("HOLIDAY", "Holiday"),
    ]

    train = models.ForeignKey("Train", on_delete=models.CASCADE, related_name="schedules")
    station = models.ForeignKey("stations.Station", on_delete=models.CASCADE)
    arrival_time = models.TimeField()
    departure_time = models.TimeField()
    day_type = models.CharField(max_length=10, choices=DAY_TYPES)
    sequence_number = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    is_active = models.BooleanField(default=True)  # Added this field
    last_updated = models.DateTimeField(auto_now=True)  # Added this field

    class Meta:
        ordering = ["sequence_number"]
        indexes = [
            models.Index(fields=["train", "day_type"]),
            models.Index(fields=["station", "arrival_time"]),
        ]

    def __str__(self):
        return f"{self.train.train_id} - {self.station.name} ({self.day_type})"


class ActualSchedule(models.Model):
    STATUS_CHOICES = [
        ("ON_TIME", "On Time"),
        ("DELAYED", "Delayed"),
        ("CANCELLED", "Cancelled"),
        ("SKIPPED", "Station Skipped"),
        ("DIVERTED", "Train Diverted"),
    ]

    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    actual_arrival = models.DateTimeField(null=True)
    actual_departure = models.DateTimeField(null=True)
    delay_minutes = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ON_TIME")
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["schedule", "status"]),
            models.Index(fields=["created_at"]),
        ]

    def save(self, *args, **kwargs):
        # Calculate delay if actual arrival time is provided
        if self.actual_arrival and self.schedule.arrival_time:
            scheduled_time = datetime.datetime.combine(self.actual_arrival.date(), self.schedule.arrival_time)
            scheduled_time = timezone.make_aware(scheduled_time)
            delay = self.actual_arrival - scheduled_time
            self.delay_minutes = max(0, int(delay.total_seconds() / 60))

            # Update status based on delay
            if self.delay_minutes == 0:
                self.status = "ON_TIME"
            elif self.delay_minutes > 0:
                self.status = "DELAYED"

        super().save(*args, **kwargs)
