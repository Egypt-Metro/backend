# apps/trains/models/schedule.py

from django.db import models
from django.core.exceptions import ValidationError
from ..constants.choices import TrainStatus


class Schedule(models.Model):
    train = models.ForeignKey('Train', on_delete=models.CASCADE, related_name='schedules')
    station = models.ForeignKey(
        'stations.Station',
        on_delete=models.CASCADE,
        related_name='train_schedules'
    )
    arrival_time = models.DateTimeField()
    departure_time = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=TrainStatus.choices,
        default=TrainStatus.IN_SERVICE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['arrival_time']
        indexes = [
            models.Index(fields=['arrival_time']),
            models.Index(fields=['station', 'arrival_time']),
        ]

    def clean(self):
        if self.departure_time <= self.arrival_time:
            raise ValidationError("Departure time must be after arrival time")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def duration(self):
        return self.departure_time - self.arrival_time

    def is_delayed(self):
        return self.status == TrainStatus.DELAYED
