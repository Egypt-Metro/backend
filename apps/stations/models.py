# apps/stations/models.py

from django.db import models
from django.core.exceptions import ValidationError
from geopy.distance import geodesic
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class Line(models.Model):
    name = models.CharField(max_length=255, unique=True)
    color_code = models.CharField(
        max_length=10,
        help_text="Format: #RRGGBB",
        null=True,
        blank=True
    )

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name

    def get_total_stations(self):
        """Get total number of stations on this line"""
        return self.stations.count()

    def get_stations_ordered(self):
        """Get stations in order"""
        return self.stations.all().order_by('station_lines__order')

    def get_first_station(self):
        """Get first station on the line"""
        return self.stations.order_by('station_lines__order').first()

    def get_last_station(self):
        """Get last station on the line"""
        return self.stations.order_by('-station_lines__order').first()

    def get_stations_in_order(self) -> List["Station"]:
        """Returns all stations on this line in order."""
        return [ls.station for ls in self.line_stations.order_by("order")]

    def get_interchanges(self) -> List["Station"]:
        """Returns all interchange stations on this line."""
        return Station.objects.filter(lines=self).filter(lines__count__gt=1).distinct()

    def get_next_station(self, current_station: "Station") -> Optional["Station"]:
        """Gets the next station on this line after the given station."""
        try:
            current_order = LineStation.objects.get(
                line=self, station=current_station
            ).order
            return Station.objects.get(
                station_lines__line=self, station_lines__order=current_order + 1
            )
        except (LineStation.DoesNotExist, Station.DoesNotExist):
            return None


class Station(models.Model):
    name = models.CharField(max_length=255, unique=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    lines = models.ManyToManyField(
        Line,
        through='LineStation',
        related_name='stations'
    )

    class Meta:
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["latitude", "longitude"]),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        if not (-90 <= self.latitude <= 90) or not (-180 <= self.longitude <= 180):
            raise ValidationError("Invalid coordinates")

    def get_connecting_lines(self) -> List[Line]:
        """Returns all lines that connect at this station."""
        return self.lines.all()

    def is_interchange(self) -> bool:
        """Checks if this is an interchange station."""
        return self.lines.count() > 1

    def is_interchange_display(self, obj):
        """Display interchange status"""
        return obj.is_interchange
    is_interchange_display.boolean = True
    is_interchange_display.short_description = "Interchange"

    def get_nearest_interchange(
        self, target_line: Line
    ) -> Optional[Tuple["Station", float]]:
        """
        Finds the nearest interchange station that connects to the target line.
        Returns (station, distance) tuple.
        """
        interchanges = (
            Station.objects.filter(lines=target_line)
            .filter(lines__in=self.lines.all())
            .exclude(id=self.id)
        )

        nearest_station = None
        min_distance = float("inf")

        for station in interchanges:
            distance = self.distance_to(station)
            if distance < min_distance:
                min_distance = distance
                nearest_station = station

        return (nearest_station, min_distance) if nearest_station else None

    def distance_to(self, other_station: "Station") -> float:
        """Calculate distance in meters to another station."""
        return geodesic(
            (self.latitude, self.longitude),
            (other_station.latitude, other_station.longitude),
        ).meters

    def get_estimated_time_to(self, destination: "Station", line: Line) -> float:
        """
        Estimates travel time to destination station on given line in minutes.
        Considers average speed and current conditions.
        """
        distance = self.distance_to(destination)
        base_time = (distance / 1000) / line.average_speed * 60  # Convert to minutes

        # Add time for stops
        stations_between = self._count_stations_between(destination, line)
        stop_time = stations_between * 1  # 1 minute per stop

        # Add delay factor based on crowd level (0-5)
        crowd_factor = 1 + (self.crowd_level * 0.1)  # Up to 50% slower

        return (base_time + stop_time) * crowd_factor

    def _count_stations_between(self, destination: "Station", line: Line) -> int:
        """Counts number of stations between this station and destination on given line."""
        try:
            start_order = LineStation.objects.get(station=self, line=line).order
            end_order = LineStation.objects.get(station=destination, line=line).order
            return abs(end_order - start_order) - 1
        except LineStation.DoesNotExist:
            return 0

    def get_all_possible_interchanges(
        self, target_line: Line
    ) -> List[Tuple["Station", float]]:
        """Returns all possible interchange stations to reach target line, sorted by distance."""
        interchanges = []
        current_lines = set(self.lines.all())

        # Find stations that connect current lines with target line
        possible_interchanges = Station.objects.filter(
            lines=target_line, lines__in=current_lines
        ).distinct()

        for interchange in possible_interchanges:
            distance = self.distance_to(interchange)
            interchanges.append((interchange, distance))

        # Sort by distance
        return sorted(interchanges, key=lambda x: x[1])

    def get_best_route_to(self, destination: "Station") -> Optional[Dict]:
        """Find the best route to destination considering all possible paths."""
        # Check if stations share a line (direct route)
        common_lines = set(self.lines.all()) & set(destination.lines.all())
        if common_lines:
            line = common_lines.pop()
            return self._get_direct_route(destination, line)

        # Need to find route with interchange
        return self._get_route_with_interchange(destination)

    def get_station_order(self, line: Line) -> int:
        """Get the order of this station on a specific line"""
        try:
            return LineStation.objects.get(
                station=self,
                line=line
            ).order
        except LineStation.DoesNotExist:
            return None

    def _get_direct_route(self, destination: "Station", line: Line) -> Dict:
        """Calculate direct route on same line."""
        start_order = self.get_station_order(line)
        end_order = destination.get_station_order(line)

        stations_between = abs(end_order - start_order) - 1
        distance = self.distance_to(destination)

        return {
            "path": self._generate_path(destination, line),
            "distance": distance,
            "num_stations": stations_between + 2,
            "interchanges": [],
        }

    def _get_route_with_interchange(self, destination: "Station") -> Optional[Dict]:
        """Find best route requiring line changes."""
        best_route = None
        min_total_distance = float("inf")

        # Try all possible combinations of interchanges
        for dest_line in destination.lines.all():
            interchanges = self.get_all_possible_interchanges(dest_line)

            for interchange, distance_to_interchange in interchanges:
                # Calculate total distance through this interchange
                distance_from_interchange = interchange.distance_to(destination)
                total_distance = distance_to_interchange + distance_from_interchange

                if total_distance < min_total_distance:
                    min_total_distance = total_distance
                    best_route = self._construct_route_through_interchange(
                        destination, interchange, dest_line
                    )

        return best_route

    def _construct_route_through_interchange(
        self, destination: "Station", interchange: "Station", dest_line: Line
    ) -> Dict:
        """Construct complete route details through an interchange station."""
        # Get lines for each segment
        start_line = (set(self.lines.all()) & set(interchange.lines.all())).pop()

        # Build complete path
        path = (
            self._generate_path(interchange, start_line)
            + interchange._generate_path(destination, dest_line)[
                1:
            ]  # Exclude duplicate interchange
        )

        return {
            "path": path,
            "distance": self.distance_to(interchange)
            + interchange.distance_to(destination),
            "num_stations": len(path),
            "interchanges": [
                {
                    "station": interchange.name,
                    "from_line": start_line.name,
                    "to_line": dest_line.name,
                }
            ],
        }

    def _generate_path(self, destination: "Station", line: Line) -> List[Dict]:
        """Generate ordered list of stations between this station and destination."""
        start_order = self.get_station_order(line)
        end_order = destination.get_station_order(line)

        # Determine direction and get stations in order
        if start_order < end_order:
            stations = line.get_stations_in_order()[start_order - 1 : end_order]
        else:
            stations = line.get_stations_in_order()[end_order - 1 : start_order][::-1]

        return [
            {"station": station.name, "line": line.name, "line_color": line.color_code}
            for station in stations
        ]


class LineStation(models.Model):
    line = models.ForeignKey(
        Line,
        on_delete=models.CASCADE,
        related_name='line_stations'
    )
    station = models.ForeignKey(
        Station,
        on_delete=models.CASCADE,
        related_name='station_lines'
    )
    order = models.PositiveIntegerField()

    class Meta:
        unique_together = ('line', 'station')
        ordering = ['order']
        indexes = [
            models.Index(fields=['line', 'order']),
        ]

    def __str__(self):
        return f"{self.line.name} - {self.station.name} (Order: {self.order})"


class ConnectingStation(models.Model):
    station = models.OneToOneField(
        Station,
        on_delete=models.CASCADE,
        related_name='connecting_station'
    )
    lines = models.ManyToManyField(Line, related_name='connecting_stations')
    transfer_time = models.IntegerField(
        default=3,
        help_text="Average transfer time in minutes"
    )

    class Meta:
        indexes = [
            models.Index(fields=['station']),
        ]

    def __str__(self):
        return f"Interchange at {self.station.name}"
