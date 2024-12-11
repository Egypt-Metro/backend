# apps/stations/models.py

from django.db import models
from geopy.distance import geodesic # type: ignore

# Create your models here.
class Line(models.Model):
    """Represents a metro line with stations connected in order."""
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


class Station(models.Model):
    name = models.CharField(max_length=255, unique=True, null=False)  # Station name
    latitude = models.FloatField(null=True, blank=True)  # GPS latitude
    longitude = models.FloatField(null=True, blank=True)  # GPS longitude
    lines = models.ManyToManyField(Line, through="LineStation", related_name="stations")

    def __str__(self):
        return self.name
    
    def connected_lines(self):
        """Returns all lines the station is connected to."""
        return self.lines.all()
    
    def is_interchange(self):
        """ Checks if the station connects to more than one line. """
        return self.lines.count() > 1

    def get_station_order(self, line):
        """
        Get the order of this station on a specific line.
        Returns None if the station is not associated with the given line.
        """
        line_station = self.station_lines.filter(line=line).first()
        return line_station.order if line_station else None
        
    def distance_to(self, other_station):
        """ Calculate distance (in meters) between two stations using lat-long."""
        start = (self.latitude, self.longitude)
        end = (other_station.latitude, other_station.longitude)
        return geodesic(start, end).meters

    def get_distance(self, user_latitude, user_longitude):
        """Calculate distance between this station and a user's location."""
        station_location = (self.latitude, self.longitude)
        user_location = (user_latitude, user_longitude)
        return geodesic(station_location, user_location).meters

    def get_next_station(self, line):
        """Returns the next station on the same line, based on the order field."""
        current_order = self.get_station_order(line)
        return Station.objects.filter(
            station_lines__line=line,
            station_lines__order__gt=current_order,
        ).order_by("station_lines__order").first()

    def get_previous_station(self, line):
        """Returns the previous station on the same line, based on the order field."""
        current_order = self.get_station_order(line)
        return Station.objects.filter(
            station_lines__line=line,
            station_lines__order__lt=current_order,
        ).order_by("-station_lines__order").first()
    
    
class LineStation(models.Model):
    """
    Through model to handle Line-Station relationship with additional metadata.
    """
    line = models.ForeignKey(Line, on_delete=models.CASCADE, related_name="line_stations")
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name="station_lines")
    order = models.PositiveIntegerField()  # Order of station on the line

    class Meta:
        unique_together = ("line", "station")  # Ensures unique line-station pairs
        ordering = ["order"]  # Default ordering by sequence in the line

    def __str__(self):
        return f"{self.line.name} - {self.station.name} (Order: {self.order})"
