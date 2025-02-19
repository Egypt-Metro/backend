import logging
import random

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.stations.models import Line, Station
from apps.trains.constants import AVERAGE_SPEEDS, CAR_CAPACITY, CARS_PER_TRAIN, LINE_CONFIG, PEAK_HOURS
from apps.trains.models import Train
from apps.trains.models.crowd import TrainCar

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Initialize trains with realistic data based on actual metro lines"

    def handle(self, *args, **kwargs):
        with transaction.atomic():
            self.stdout.write("Initializing trains...")

            # Delete existing trains
            Train.objects.all().delete()

            # Get all lines and log their names
            lines = Line.objects.all()
            self.stdout.write(f"Found lines: {', '.join([line.name for line in lines])}")

            for line in lines:
                line_name = f"LINE_{line.name}"
                config = LINE_CONFIG.get(line_name)

                if not config:
                    self.stdout.write(
                        self.style.WARNING(
                            f"No config for line {line.name}. " f'Available configs: {", ".join(LINE_CONFIG.keys())}'
                        )
                    )
                    continue

                # Get actual stations for this line
                stations = Station.objects.filter(lines=line).order_by("station_lines__order")

                self.stdout.write(f"Processing {line.name}: Found {stations.count()} stations")

                if not stations.exists():
                    self.stdout.write(self.style.WARNING(f"No stations found for {line.name}"))
                    continue

                # Calculate trains needed
                total_trains = config["total_trains"]
                ac_trains = int((config["has_ac_percentage"] / 100) * total_trains)
                station_spacing = max(1, stations.count() // total_trains)

                self.stdout.write(
                    f"Creating {ac_trains} AC and {total_trains - ac_trains} " f"non-AC trains for {line.name}"
                )

                try:
                    # Create AC trains
                    for i in range(ac_trains):
                        station_index = (i * station_spacing) % stations.count()
                        train = self._create_train(line, i + 1, True, stations, station_index, config)
                        self._create_cars(train, is_peak=self._is_peak_hour())

                    # Create non-AC trains
                    for i in range(total_trains - ac_trains):
                        station_index = ((i + ac_trains) * station_spacing) % stations.count()
                        train = self._create_train(line, i + ac_trains + 1, False, stations, station_index, config)
                        self._create_cars(train, is_peak=self._is_peak_hour())

                    self.stdout.write(self.style.SUCCESS(f"Created {total_trains} trains for {line.name}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error creating trains for {line.name}: {str(e)}"))

    def _create_train(self, line, number, has_ac, stations, station_index, config):
        """Create a train with realistic data"""
        try:
            current_station = stations[station_index]
            next_station = stations[station_index + 1] if station_index < len(stations) - 1 else stations[0]

            # Get direction based on station order
            direction = self._determine_direction(line, current_station, next_station)

            # Determine status
            is_peak = self._is_peak_hour()
            status = "IN_SERVICE" if (is_peak or random.random() > 0.1) else random.choice(["DELAYED", "MAINTENANCE"])

            # Convert and round coordinates to Decimal with 6 decimal places
            from decimal import ROUND_DOWN, Decimal

            try:
                lat = Decimal(str(current_station.latitude)).quantize(Decimal("0.000001"), rounding=ROUND_DOWN)
                lon = Decimal(str(current_station.longitude)).quantize(Decimal("0.000001"), rounding=ROUND_DOWN)
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Error converting coordinates: {e}"))
                lat = Decimal("0.000000")
                lon = Decimal("0.000000")

            train = Train.objects.create(
                train_id=f'{line.name}_{number:03d}_{"AC" if has_ac else "NONAC"}',
                line=line,
                has_air_conditioning=has_ac,
                number_of_cars=CARS_PER_TRAIN,
                current_station=current_station,
                next_station=next_station,
                direction=direction,
                status=status,
                speed=self._calculate_speed(config, is_peak),
                latitude=lat,
                longitude=lon,
                last_updated=timezone.now(),
            )

            self.stdout.write(f"Created train: {train.train_id}")
            return train

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating train: {str(e)}"))
            raise

    def _create_cars(self, train, is_peak):
        """Create cars for a train with appropriate capacity settings"""
        try:
            cars_created = []
            for car_number in range(1, train.number_of_cars + 1):
                # Calculate initial load based on peak hours
                initial_load = random.randint(0, int(CAR_CAPACITY["TOTAL"] * (0.8 if is_peak else 0.4)))

                car = TrainCar.objects.create(
                    train=train,
                    car_number=car_number,
                    capacity=CAR_CAPACITY["TOTAL"],
                    current_load=initial_load,
                    is_operational=True,
                )
                cars_created.append(car)

            self.stdout.write(f"Created {len(cars_created)} cars for train {train.train_id}")
            return cars_created

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error creating cars for train {train.train_id}: {str(e)}"))
            return []

    def _is_peak_hour(self):
        """
        Determine if current time is during peak hours
        Returns True if current time is during morning or evening peak hours
        """
        current_time = timezone.localtime().time()

        # Convert peak hour strings to time objects
        morning_start = timezone.datetime.strptime(PEAK_HOURS["MORNING"]["start"], "%H:%M").time()
        morning_end = timezone.datetime.strptime(PEAK_HOURS["MORNING"]["end"], "%H:%M").time()
        evening_start = timezone.datetime.strptime(PEAK_HOURS["EVENING"]["start"], "%H:%M").time()
        evening_end = timezone.datetime.strptime(PEAK_HOURS["EVENING"]["end"], "%H:%M").time()

        # Check if current time is in either morning or evening peak hours
        is_morning_peak = morning_start <= current_time <= morning_end
        is_evening_peak = evening_start <= current_time <= evening_end

        return is_morning_peak or is_evening_peak

    def _calculate_speed(self, config, is_peak):
        """
        Calculate train speed based on configuration and peak hours
        """
        base_speed = config["speed_limit"]
        if is_peak:
            return min(AVERAGE_SPEEDS["PEAK"], base_speed)
        return min(AVERAGE_SPEEDS["NORMAL"], base_speed)

    def _determine_direction(self, line, current_station, next_station):
        """Determine train direction based on station order"""
        try:
            current_order = current_station.get_station_order(line)
            next_order = next_station.get_station_order(line)

            line_config = LINE_CONFIG[f"LINE_{line.name}"]
            directions = line_config["directions"]

            # Default to first direction if order comparison fails
            if current_order is None or next_order is None:
                return directions[0][0]

            return directions[0][0] if next_order > current_order else directions[1][0]

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error determining direction: {str(e)}"))
            # Return default direction
            return LINE_CONFIG[f"LINE_{line.name}"]["directions"][0][0]
