# apps/routes/models.py

from django.db import models


class PrecomputedRoute(models.Model):
    """Stores precomputed shortest paths to optimize performance."""
    start_station = models.ForeignKey("stations.Station", on_delete=models.CASCADE, related_name="route_starts")
    end_station = models.ForeignKey("stations.Station", on_delete=models.CASCADE, related_name="route_ends")
    distance = models.FloatField(help_text="Distance in meters")
    duration = models.FloatField(help_text="Estimated travel time in minutes")
    path = models.JSONField(help_text="Ordered list of station IDs forming the route")

    class Meta:
        verbose_name_plural = "Precomputed Routes"
        unique_together = ("start_station", "end_station")  # Ensure unique routes
        indexes = [
            models.Index(fields=["start_station", "end_station"]),  # Optimize lookups
        ]

    def __str__(self):
        return f"{self.start_station.name} → {self.end_station.name}"
