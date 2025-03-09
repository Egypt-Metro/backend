# apps/trains/management/commands/generate_test_data.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import random
import logging
from typing import List, Dict, Any, Optional, Tuple
from apps.trains.models import Train, TrainCar, Schedule
from apps.stations.models import Station, Line
from apps.trains.constants.choices import (
    TrainStatus, CrowdLevel, Direction, 
    CARS_PER_TRAIN, MAX_SCHEDULES, CROWD_THRESHOLDS
)

logger = logging.getLogger(__name__)


class LineConfiguration:
    """Configuration class for metro lines"""
    CONFIGS = [
        {
            "name": "First Line",
            "color": "#FF0000",
            "directions": [Direction.HELWAN, Direction.MARG],
            "has_ac_percentage": 50,
            "camera_cars_per_direction": 10,
            "cars_per_train": CARS_PER_TRAIN
        },
        {
            "name": "Second Line",
            "color": "#008000",
            "directions": [Direction.SHOBRA, Direction.MONIB],
            "has_ac_percentage": 50,
            "camera_cars_per_direction": 10,
            "cars_per_train": CARS_PER_TRAIN
        },
        {
            "name": "Third Line",
            "color": "#0000FF",
            "directions": [Direction.ADLY, Direction.KIT_KAT],
            "has_ac_percentage": 100,
            "camera_cars_per_direction": 10,
            "cars_per_train": CARS_PER_TRAIN
        }
    ]

    @classmethod
    def get_config(cls, line_name: Optional[str] = None) -> List[Dict[str, Any]]:
        if line_name:
            return [config for config in cls.CONFIGS if config["name"] == line_name]
        return cls.CONFIGS


class DataGenerator:
    """Helper class for generating test data"""

    @staticmethod
    def get_weighted_status() -> str:
        statuses: List[Tuple[str, int]] = [
            (TrainStatus.IN_SERVICE.value, 70),
            (TrainStatus.DELAYED.value, 15),
            (TrainStatus.MAINTENANCE.value, 10),
            (TrainStatus.OUT_OF_SERVICE.value, 5)
        ]
        return random.choices(
            [status for status, _ in statuses],
            weights=[weight for _, weight in statuses],
            k=1
        )[0]

    @staticmethod
    def get_base_passenger_count() -> int:
        hour = timezone.now().hour
        if 6 <= hour <= 9:  # Morning rush
            return random.randint(20, 30)
        elif 16 <= hour <= 19:  # Evening rush
            return random.randint(25, 30)
        elif 10 <= hour <= 15:  # Mid-day
            return random.randint(10, 20)
        else:  # Early morning or late night
            return random.randint(5, 15)

    @staticmethod
    def calculate_car_passengers(base: int) -> int:
        variation = random.uniform(0.7, 1.3)
        return min(30, max(0, int(base * variation)))

    @staticmethod
    def calculate_crowd_level(passengers: int) -> str:
        for level, (min_val, max_val) in CROWD_THRESHOLDS.items():
            if min_val <= passengers <= max_val:
                return level.value
        return CrowdLevel.FULL.value


class Command(BaseCommand):
    help = 'Generate test data for trains, cars, and schedules'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stats = {
            'trains_created': 0,
            'cars_created': 0,
            'schedules_created': 0
        }
        self.data_generator = DataGenerator()

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing trains data before generating new data'
        )
        parser.add_argument(
            '--line',
            type=str,
            help='Generate data for specific line (e.g., "First Line")'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force data generation without confirmation'
        )

    @transaction.atomic
    def handle(self, *args, **kwargs):
        try:
            self._initialize_generation(kwargs)
            lines_to_process = LineConfiguration.get_config(kwargs.get('line'))

            if not lines_to_process:
                self.stdout.write(self.style.WARNING('No lines to process'))
                return

            for line_config in lines_to_process:
                self._process_line(line_config)

            self._display_summary()

        except Exception as e:
            logger.error(f"Error generating test data: {str(e)}")
            self.stdout.write(self.style.ERROR(f"Failed to generate test data: {str(e)}"))
            raise

    def _initialize_generation(self, kwargs: Dict[str, Any]) -> None:
        """Initialize data generation process"""
        if not self._validate_prerequisites():
            raise ValueError("Prerequisites not met")

        existing_data = self._check_existing_data()
        if any(existing_data.values()):
            if kwargs.get('clear') or kwargs.get('force') or self._confirm_clear(existing_data):
                self._clear_existing_data()
            else:
                raise ValueError("Cannot proceed with existing data")

    def _validate_prerequisites(self) -> bool:
        """Validate required data exists"""
        if not Line.objects.exists():
            self.stdout.write(self.style.ERROR('No lines found. Please create lines first.'))
            return False

        if not Station.objects.exists():
            self.stdout.write(self.style.ERROR('No stations found. Please create stations first.'))
            return False

        return True

    def _check_existing_data(self) -> Dict[str, int]:
        """Check if there's existing data"""
        return {
            'trains': Train.objects.count(),
            'cars': TrainCar.objects.count(),
            'schedules': Schedule.objects.count()
        }

    def _confirm_clear(self, existing_data: Dict[str, int]) -> bool:
        """Ask for confirmation before clearing data"""
        self.stdout.write(
            self.style.WARNING(
                f'\nFound existing data:\n'
                f'- {existing_data["trains"]} trains\n'
                f'- {existing_data["cars"]} train cars\n'
                f'- {existing_data["schedules"]} schedules\n'
                'Do you want to clear this data before proceeding? [y/N]: '
            )
        )
        return input().lower() == 'y'

    def _clear_existing_data(self) -> None:
        """Clear all existing data"""
        with transaction.atomic():
            try:
                Schedule.objects.all().delete()
                TrainCar.objects.all().delete()
                Train.objects.all().delete()
                self.stdout.write(self.style.SUCCESS('Existing data cleared successfully'))
            except Exception as e:
                logger.error(f"Error clearing data: {str(e)}")
                raise

    def _process_line(self, line_config: Dict[str, Any]) -> None:
        """Process a single line configuration"""
        try:
            line = Line.objects.get(name=line_config["name"])
            stations = Station.objects.filter(lines=line).order_by('station_lines__order')

            if not stations.exists():
                self.stdout.write(
                    self.style.WARNING(f'No stations found for {line.name}, skipping...')
                )
                return

            self.stdout.write(f'\nProcessing {line.name}:')

            for direction in line_config["directions"]:
                self._generate_trains_for_direction(
                    line,
                    direction,
                    stations,
                    line_config
                )

        except Line.DoesNotExist:
            logger.warning(f"Line {line_config['name']} not found")
            self.stdout.write(
                self.style.WARNING(f'Line {line_config["name"]} not found, skipping...')
            )
        except Exception as e:
            logger.error(f"Error processing line {line_config['name']}: {str(e)}")
            raise

    def _generate_trains_for_direction(
        self,
        line: Line,
        direction: str,
        stations: List[Station],
        line_config: Dict[str, Any]
    ) -> None:
        """Generate trains for a specific direction"""
        num_trains = stations.count() * 2  # 2 trains per station

        self.stdout.write(f'  Generating {num_trains} trains for direction {direction}')

        for i in range(1, num_trains + 1):
            try:
                with transaction.atomic():
                    train = self._create_train(line, direction, i, stations, line_config)
                    self._create_cars(train, line_config)
                    self._create_schedules(train, stations)

                self.stats['trains_created'] += 1
                if i % 10 == 0:
                    self.stdout.write(f'    Created {i} trains...')

            except Exception as e:
                logger.error(f"Error generating train {i} for {line.name} {direction}: {str(e)}")
                raise

    def _create_train(
        self,
        line: Line,
        direction: str,
        number: int,
        stations: List[Station],
        line_config: Dict[str, Any]
    ) -> Train:
        """Create a single train"""
        return Train.objects.create(
            train_number=f"T{line.name[0]}{direction[:1]}{number:03d}",
            line=line,
            status=self.data_generator.get_weighted_status(),
            has_ac=random.randint(1, 100) <= line_config["has_ac_percentage"],
            direction=direction,
            current_station=random.choice(stations),
            camera_car_number=(
                random.randint(1, CARS_PER_TRAIN)
                if number <= line_config["camera_cars_per_direction"]
                else None
            )
        )

    def _create_cars(self, train: Train, line_config: Dict[str, Any]) -> None:
        """Create cars for a train"""
        base_passengers = self.data_generator.get_base_passenger_count()

        for car_number in range(1, line_config["cars_per_train"] + 1):
            try:
                passengers = self.data_generator.calculate_car_passengers(base_passengers)

                car, created = TrainCar.objects.get_or_create(
                    train=train,
                    car_number=car_number,
                    defaults={
                        'has_camera': (car_number == train.camera_car_number),
                        'current_passengers': passengers,
                        'crowd_level': self.data_generator.calculate_crowd_level(passengers)
                    }
                )

                if created:
                    self.stats['cars_created'] += 1

            except Exception as e:
                logger.error(
                    f"Error creating car {car_number} for train {train.train_number}: {str(e)}"
                )
                raise

    def _create_schedules(self, train: Train, stations: List[Station]) -> None:
        """Create schedules for a train"""
        base_time = timezone.now()
        station_list = self._get_ordered_stations(train, stations)
        current_index = station_list.index(train.current_station)

        # Only create schedules for the next MAX_SCHEDULES stations
        future_stations = station_list[current_index:current_index + MAX_SCHEDULES]

        for idx, station in enumerate(future_stations):
            try:
                # Add some randomness to arrival times
                delay = random.randint(-2, 2) if train.status == TrainStatus.DELAYED.value else 0
                arrival_time = base_time + timedelta(minutes=(idx * 3) + delay)

                Schedule.objects.create(
                    train=train,
                    station=station,
                    arrival_time=arrival_time,
                    departure_time=arrival_time + timedelta(minutes=1),
                    status=train.status
                )
                self.stats['schedules_created'] += 1

            except Exception as e:
                logger.error(
                    f"Error creating schedule for train {train.train_number} at station {station.name}: {str(e)}"
                )
                raise

    def _get_ordered_stations(self, train: Train, stations: List[Station]) -> List[Station]:
        """Get ordered list of stations based on direction"""
        station_list = list(stations)
        if train.direction in [Direction.MARG, Direction.MONIB, Direction.KIT_KAT]:
            station_list.reverse()
        return station_list

    def _display_summary(self) -> None:
        """Display summary of generated data"""
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully generated test data:\n'
                f'- {self.stats["trains_created"]} trains\n'
                f'- {self.stats["cars_created"]} train cars\n'
                f'- {self.stats["schedules_created"]} schedules'
            )
        )
