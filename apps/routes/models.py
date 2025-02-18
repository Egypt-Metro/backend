# apps/routes/models.py

from django.db import models
from django.utils import timezone
from apps.stations.models import Line, Station
import logging

logger = logging.getLogger(__name__)


class Route(models.Model):
    """Model for storing routes between stations"""

    start_station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name='routes_from'
    )
    end_station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name='routes_to'
    )
    total_distance = models.FloatField(
        help_text="Total distance in meters",
        default=0
    )
    total_time = models.IntegerField(
        help_text="Estimated time in minutes",
        default=0
    )
    path = models.JSONField(
        help_text="Ordered list of stations and lines in the route",
        default=list
    )
    interchanges = models.JSONField(
        help_text="List of interchange points",
        default=list,
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    number_of_stations = models.IntegerField(default=0)
    primary_line = models.ForeignKey(
        Line,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='primary_routes'
    )

    class Meta:
        verbose_name = "Route"
        verbose_name_plural = "Routes"
        unique_together = ('start_station', 'end_station')
        indexes = [
            models.Index(fields=['start_station', 'end_station']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_active']),
            models.Index(fields=['primary_line']),
        ]

    def save(self, *args, **kwargs):
        # Calculate number of stations from path
        if self.path:
            self.number_of_stations = len([
                station for station in self.path
                if isinstance(station, dict) and 'station' in station
            ])

        # Set primary line
        if self.path and isinstance(self.path, list) and len(self.path) > 0:
            first_segment = self.path[0]
            if isinstance(first_segment, dict) and 'line' in first_segment:
                try:
                    self.primary_line = Line.objects.get(name=first_segment['line'])
                except Line.DoesNotExist:
                    logger.warning(f"Line not found: {first_segment['line']}")
                    self.primary_line = None

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Route: {self.start_station.name} -> {self.end_station.name}"
