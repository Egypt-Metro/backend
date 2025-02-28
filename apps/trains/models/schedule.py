# apps/trains/models/schedule.py

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from ..constants import ScheduleStatus, CrowdLevel


class Schedule(models.Model):
    """
    Model for train schedules focusing on arrival times at stations.
    Handles schedule tracking and status management.
    """

    # Core fields with explicit related_name
    train = models.ForeignKey(
        'Train',
        on_delete=models.CASCADE,
        related_name='schedules',
        help_text="Train assigned to this schedule"
    )
    station = models.ForeignKey(
        'stations.Station',
        on_delete=models.CASCADE,
        related_name='train_schedules',
        help_text="Station for this schedule"
    )

    # Timing field
    arrival_time = models.DateTimeField(
        db_index=True,
        help_text="Expected arrival time at the station"
    )

    # Status fields
    status = models.CharField(
        max_length=10,
        choices=ScheduleStatus.choices,
        default=ScheduleStatus.ON_TIME,
        help_text="Current status of the schedule"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this schedule is currently active"
    )

    # Crowd information
    expected_crowd_level = models.CharField(
        max_length=10,
        choices=CrowdLevel.choices,
        default=CrowdLevel.MODERATE,
        help_text="Expected crowding level at the station"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['station', 'arrival_time']),
            models.Index(fields=['train', 'arrival_time']),
        ]
        ordering = ['arrival_time']
        verbose_name = 'Train Schedule'
        verbose_name_plural = 'Train Schedules'

    def __str__(self):
        return (
            f"Train {self.train.train_id} at {self.station.name} - "
            f"{self.arrival_time.strftime('%Y-%m-%d %H:%M')}"
        )

    def clean(self):
        """Validate schedule data"""
        if self.arrival_time < timezone.now():
            raise ValidationError("Arrival time cannot be in the past")

    def save(self, *args, **kwargs):
        """Override save to ensure data validation"""
        self.full_clean()
        super().save(*args, **kwargs)

    # Properties
    @property
    def is_delayed(self) -> bool:
        """Check if schedule is delayed"""
        return self.status == ScheduleStatus.DELAYED

    @property
    def is_cancelled(self) -> bool:
        """Check if schedule is cancelled"""
        return self.status == ScheduleStatus.CANCELLED

    @property
    def delay_duration(self) -> int:
        """Calculate delay duration in minutes"""
        if not self.is_delayed:
            return 0
        delay = timezone.now() - self.arrival_time
        return max(0, int(delay.total_seconds() / 60))

    # Methods
    def update_status(self, new_status: str, new_arrival_time=None):
        """Update schedule status and optionally arrival time"""
        if new_status not in ScheduleStatus.values:
            raise ValueError(f"Invalid status: {new_status}")

        self.status = new_status
        if new_arrival_time:
            self.arrival_time = new_arrival_time
        self.save()

    def cancel(self):
        """Cancel this schedule"""
        self.status = ScheduleStatus.CANCELLED
        self.is_active = False
        self.save()

    @classmethod
    def get_active_schedules(cls, station_id: int, time_window: int = 120):
        """Get active schedules for a station within time window"""
        current_time = timezone.now()
        end_time = current_time + timezone.timedelta(minutes=time_window)

        return cls.objects.filter(
            station_id=station_id,
            arrival_time__gte=current_time,
            arrival_time__lte=end_time,
            is_active=True
        ).select_related('train', 'station')
