# apps/trains/management/commands/generate_schedules.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import logging

from apps.trains.models import Train, Schedule
from apps.stations.models import Station
from apps.trains.constants import DWELL_TIMES, AVERAGE_SPEEDS

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Generate realistic schedules for trains"

    def handle(self, *args, **kwargs):
        try:
            with transaction.atomic():
                self.stdout.write("Generating schedules...")

                # Clear existing schedules
                Schedule.objects.all().delete()

                # Get active trains
                trains = Train.objects.filter(status="IN_SERVICE")
                if not trains.exists():
                    self.stdout.write(
                        self.style.ERROR(
                            "No active trains found. Run initialize_trains first."
                        )
                    )
                    return

                current_time = timezone.now()
                schedules_created = 0

                for train in trains:
                    # Get stations for this train's line in order
                    stations = Station.objects.filter(lines=train.line).order_by(
                        "station_lines__order"
                    )

                    if not stations.exists():
                        continue

                    # Generate schedules for next 3 hours
                    self._generate_train_schedules(
                        train=train, stations=stations, start_time=current_time, hours=3
                    )
                    schedules_created += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully generated schedules for {schedules_created} trains"
                    )
                )

        except Exception as e:
            logger.error(f"Error generating schedules: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f"Failed to generate schedules: {str(e)}")
            )

    def _generate_train_schedules(self, train, stations, start_time, hours):
        """Generate schedules for a train considering its direction."""
        try:
            current_time = start_time

            # Get stations in the correct order based on train direction
            ordered_stations = list(stations)
            if train.direction == train.line.get_last_station().name:
                ordered_stations = list(reversed(ordered_stations))

            # Find current station index
            current_index = ordered_stations.index(train.current_station)

            # Generate schedules starting from current station
            for hour in range(hours):
                hour_start = start_time + timedelta(hours=hour)
                current_time = hour_start

                # Generate schedules for remaining stations in direction
                for idx in range(current_index, len(ordered_stations)):
                    station = ordered_stations[idx]

                    if idx == current_index:
                        arrival_time = current_time
                    else:
                        prev_station = ordered_stations[idx - 1]

                        # Calculate travel time
                        distance = prev_station.distance_to(station)
                        speed = AVERAGE_SPEEDS['PEAK'] if self._is_peak_hour() else AVERAGE_SPEEDS['NORMAL']
                        travel_time = (distance / speed) * 3600  # Convert to seconds

                        # Add dwell time
                        dwell_time = self._get_dwell_time(prev_station)

                        # Calculate arrival time
                        arrival_time = current_time + timedelta(seconds=int(travel_time + dwell_time))

                    # Create schedule
                    Schedule.objects.create(
                        train=train,
                        station=station,
                        arrival_time=arrival_time,
                        status='ON_TIME',
                        is_active=True,
                        expected_crowd_level=self._predict_crowd_level(station, arrival_time)
                    )

                    current_time = arrival_time

                # Reset for next round if needed
                current_index = 0

            return True

        except Exception as e:
            logger.error(f"Error generating schedules for train {train.train_id}: {str(e)}")
            raise

    def _get_dwell_time(self, station):
        """Calculate dwell time for a station."""
        base_time = DWELL_TIMES["NORMAL"]

        # Adjust for station type
        if station.is_interchange:
            base_time = DWELL_TIMES["INTERCHANGE"]
        elif station.is_terminal:
            base_time = DWELL_TIMES["TERMINAL"]

        # Adjust for peak hours
        if self._is_peak_hour():
            base_time *= DWELL_TIMES["PEAK_FACTOR"]

        return base_time

    def _predict_crowd_level(self, station, time):
        """Predict crowd level based on station and time."""
        hour = time.hour

        # Simple crowd prediction logic
        if 7 <= hour <= 10 or 16 <= hour <= 19:  # Peak hours
            return "HIGH"
        elif 11 <= hour <= 15:  # Mid-day
            return "MODERATE"
        else:
            return "LOW"

    def _is_peak_hour(self):
        """Check if current time is during peak hours."""
        current_time = timezone.now().time()
        morning_peak = 7 <= current_time.hour <= 10
        evening_peak = 16 <= current_time.hour <= 19
        return morning_peak or evening_peak

    def _calculate_distance(self, station1, station2):
        """Calculate distance between two stations in kilometers."""
        try:
            # Use the Haversine formula if you have coordinates
            from math import radians, sin, cos, sqrt, atan2

            lat1, lon1 = radians(station1.latitude), radians(station1.longitude)
            lat2, lon2 = radians(station2.latitude), radians(station2.longitude)

            dlat = lat2 - lat1
            dlon = lon2 - lon1

            a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
            c = 2 * atan2(sqrt(a), sqrt(1 - a))

            # Earth's radius in kilometers
            R = 6371

            return R * c
        except Exception:
            # Fallback to average distance between metro stations if coordinates not available
            return 1.2  # Average distance between metro stations in km
