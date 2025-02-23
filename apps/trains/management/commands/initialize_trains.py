from decimal import ROUND_DOWN, Decimal, DecimalException
import logging
import random

from dj_database_url import config
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

            # Clear existing data
            Train.objects.all().delete()
            TrainCar.objects.all().delete()

            # Get all lines and log their names
            lines = Line.objects.all()
            self.stdout.write(f"Found lines: {', '.join([line.name for line in lines])}")

            for line in lines:
                # Remove spaces and special characters from line name
                formatted_line_name = line.name.replace(" ", "_")
                line_config_key = f"LINE_{formatted_line_name}"
                config = LINE_CONFIG.get(line_config_key)

                if not config:
                    self.stdout.write(
                        self.style.WARNING(
                            f"No config for line {line.name}. "
                            f'Available configs: {", ".join(LINE_CONFIG.keys())}'
                        )
                    )
                    continue

                # Get actual stations for this line
                stations = Station.objects.filter(lines=line).order_by("station_lines__order")
                station_count = stations.count()

                self.stdout.write(f"Processing {line.name}: Found {station_count} stations")

                if not station_count:
                    self.stdout.write(self.style.WARNING(f"No stations found for {line.name}"))
                    continue

                # Calculate trains needed
                total_trains = config["total_trains"]
                ac_trains = int((config["has_ac_percentage"] / 100) * total_trains)
                station_spacing = max(1, station_count // total_trains)

                self.stdout.write(
                    f"Creating {ac_trains} AC and {total_trains - ac_trains} "
                    f"non-AC trains for {line.name}"
                )

                try:
                    # Create AC trains
                    for i in range(ac_trains):
                        station_index = (i * station_spacing) % station_count
                        train = self._create_train(line, i + 1, True, stations, station_index, config)
                        self._create_cars(train, is_peak=self._is_peak_hour())

                    # Create non-AC trains
                    for i in range(total_trains - ac_trains):
                        station_index = ((i + ac_trains) * station_spacing) % station_count
                        train = self._create_train(
                            line, i + ac_trains + 1, False, stations, station_index, config
                        )
                        self._create_cars(train, is_peak=self._is_peak_hour())

                    self.stdout.write(self.style.SUCCESS(f"Created {total_trains} trains for {line.name}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error creating trains for {line.name}: {str(e)}"))

    def _create_train(self, line, number, has_ac, station_list, station_index, config):
        """
        Create a train with comprehensive error handling and validation.

        Args:
            line: Line object
            number: Train number within the line
            has_ac: Boolean indicating AC status
            stations: QuerySet of stations
            station_index: Current station index
            config: Line configuration dictionary

        Returns:
            Train object
        """
        try:
            # Validate input parameters
            if not all([line, station_list, config]):
                raise ValueError("Missing required parameters")

            # Get current and next stations with validation
            try:
                current_station = station_list[station_index]
                next_station = station_list[station_index + 1] if station_index < len(station_list) - 1 else station_list[0]
            except IndexError as e:
                raise ValueError(f"Invalid station index: {station_index}") from e

            # Get direction based on station order
            current_order = current_station.get_station_order(line)
            next_order = next_station.get_station_order(line)

            # Use directions from the passed config
            directions = config["directions"]

            if current_order is None or next_order is None:
                self.stdout.write(self.style.WARNING(
                    f"Station order not found for line {line.name}: "
                    f"Current: {current_station.name}, Next: {next_station.name}"
                ))
                direction = directions[0][0]  # Default direction
            else:
                direction = directions[0][0] if next_order > current_order else directions[1][0]

            # Generate train_id with validation
            line_mapping = {
                'First': '1',
                'Second': '2',
                'Third': '3'
            }

            line_number = line_mapping.get(line.name.split()[0])
            if not line_number:
                raise ValueError(f"Invalid line name format: {line.name}")

            # Convert train_id to string format
            train_id = f"{line_number}{number:03d}"

            # Handle coordinates
            try:
                lat = Decimal(str(current_station.latitude or 0)).quantize(
                    Decimal("0.000001"),
                    rounding=ROUND_DOWN
                )
                lon = Decimal(str(current_station.longitude or 0)).quantize(
                    Decimal("0.000001"),
                    rounding=ROUND_DOWN
                )
            except (TypeError, DecimalException) as e:
                self.stdout.write(self.style.WARNING(f"Error converting coordinates: {e}"))
                lat, lon = Decimal("0.000000"), Decimal("0.000000")

            # Determine status
            is_peak = self._is_peak_hour()
            status = (
                "IN_SERVICE"
                if (is_peak or random.random() > 0.1)
                else random.choice(["DELAYED", "MAINTENANCE"])
            )

            # Create train
            train = Train.objects.create(
                train_id=train_id,
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

            self.stdout.write(
                self.style.SUCCESS(
                    f"Created train {train.train_id} on line {line.name}\n"
                    f"Direction: {direction} ({current_station.name} → {next_station.name})\n"
                    f"Status: {status}, AC: {has_ac}"
                )
            )
            return train

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f"Error creating train for line {line.name}:\n"
                    f"Error type: {type(e).__name__}\n"
                    f"Error message: {str(e)}"
                )
            )
            raise

        except Exception as e:
            # Log detailed error information
            self.stdout.write(
                self.style.ERROR(
                    f"Error creating train for line {line.name}:\n"
                    f"Error type: {type(e).__name__}\n"
                    f"Error message: {str(e)}"
                )
            )
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
            directions = config["directions"]

            # Log station orders for debugging
            self.stdout.write(
                f"Determining direction for line {line.name}: "
                f"Current station ({current_station.name}) order: {current_order}, "
                f"Next station ({next_station.name}) order: {next_order}"
            )

            if current_order is None or next_order is None:
                self.stdout.write(f"Using default direction {directions[0][0]}")
                return directions[0][0]

            direction = directions[0][0] if next_order > current_order else directions[1][0]
            self.stdout.write(f"Selected direction: {direction}")
            return direction

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error determining direction: {str(e)}"))
            return config["directions"][0][0]
