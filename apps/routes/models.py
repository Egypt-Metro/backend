# apps/routes/models.py

import logging
from django.db import models
from apps.stations.models import Station, Line

logger = logging.getLogger(__name__)


def get_default_line():
    """Fetches the first available Line object ID or returns None if none exist."""
    line = Line.objects.first()
    if line:
        return line.id
    logger.warning("No Line objects exist. Please add at least one Line.")
    return None


class PrecomputedRoute(models.Model):
    """Stores precomputed shortest paths to optimize performance."""

    start_station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="route_starts")
    end_station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="route_ends")
    line = models.ForeignKey(Line, on_delete=models.CASCADE, default=get_default_line)
    path = models.JSONField(help_text="Ordered list of station IDs forming the route")
    interchanges = models.JSONField(help_text="List of interchanges with corresponding lines", null=True, blank=True)

    class Meta:
        verbose_name_plural = "Precomputed Routes"
        unique_together = ("start_station", "end_station", "line")  # Ensuring unique routes per line
        indexes = [
            models.Index(fields=["start_station", "end_station", "line"]),  # Optimized indexing
        ]

    def __str__(self):
        return f"{self.start_station.name} → {self.end_station.name} via {self.line.name}"
