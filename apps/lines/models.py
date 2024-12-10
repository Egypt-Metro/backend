# apps/lines/models.py
from django.db import models

# Create your models here.
class Line(models.Model):
    name = models.CharField(max_length=255, unique=True, null=False)  # Line name
    color_code = models.CharField(
        max_length=10, null=True, blank=True, help_text="Format: #RRGGBB"
    )  # Optional color code

    def __str__(self):
        return self.name

    def total_stations(self):
        """Returns the total number of stations on this line."""
        return self.line_stations.count()
    
    def ordered_stations(self):
        """Returns all stations in order."""
        return self.line_stations.order_by("order")