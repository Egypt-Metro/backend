# apps/stations/services/station_service.py

import datetime
from typing import Tuple, Optional
from django.utils import timezone
from apps.stations.models import Station, Line


class StationService:
    @staticmethod
    def find_best_interchange(
        start_station: Station,
        end_station: Station
    ) -> Optional[Tuple[Station, Line, Line]]:
        """
        Finds the best interchange station between two stations on different lines.
        Returns (interchange_station, from_line, to_line).
        """
        start_lines = set(start_station.lines.all())
        end_lines = set(end_station.lines.all())

        # If stations share a line, no interchange needed
        common_lines = start_lines.intersection(end_lines)
        if common_lines:
            return None

        # Find all possible interchange stations
        possible_interchanges = Station.objects.filter(
            lines__in=start_lines
        ).filter(
            lines__in=end_lines
        ).distinct()

        best_interchange = None
        min_total_distance = float('inf')

        for interchange in possible_interchanges:
            # Calculate total distance through this interchange
            distance_to_interchange = start_station.distance_to(interchange)
            distance_from_interchange = interchange.distance_to(end_station)
            total_distance = distance_to_interchange + distance_from_interchange

            if total_distance < min_total_distance:
                min_total_distance = total_distance
                best_interchange = interchange

        if best_interchange:
            from_line = (start_lines & set(best_interchange.lines.all())).pop()
            to_line = (end_lines & set(best_interchange.lines.all())).pop()
            return (best_interchange, from_line, to_line)

        return None

    # @staticmethod
    # def calculate_fare(distance: float) -> float:
    #     """
    #     Calculates fare based on distance and current pricing rules.
    #     """
    #     base_fare = 5.0  # Base fare in currency units
    #     distance_fare = distance * 0.1  # 0.1 per meter
    #     return base_fare + distance_fare

    @staticmethod
    def estimate_crowd_level(station: Station, time: datetime) -> int:
        """
        Estimates crowd level (0-5) at a station for a given time.
        """
        # Implementation would consider historical data, time of day, events, etc.
        pass

    @staticmethod
    def is_operating(station: Station, time: datetime = None) -> bool:
        """Check if station is operating at given time"""
        if not time:
            time = timezone.now()

        # Get operational hours for current day
        day_name = time.strftime('%A').lower()
        hours = station.lines.first().operational_hours.get(day_name, {})

        if not hours:
            return False

        opening_time = datetime.strptime(hours['open'], '%H:%M').time()
        closing_time = datetime.strptime(hours['close'], '%H:%M').time()
        current_time = time.time()

        return opening_time <= current_time <= closing_time
