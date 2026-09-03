# apps/trains/tests/factories.py

from datetime import timedelta

import factory
from django.utils import timezone
from factory.django import DjangoModelFactory

from apps.stations.models import Line, Station
from apps.trains.constants.choices import CARS_PER_TRAIN, CrowdLevel, Direction, TrainStatus
from apps.trains.models import Schedule, Train, TrainCar


class LineFactory(DjangoModelFactory):
    class Meta:
        model = Line
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Line {n + 1}")
    color_code = factory.Sequence(lambda n: f"#{(n * 111) % 0xFFFFFF:06X}")


class StationFactory(DjangoModelFactory):
    class Meta:
        model = Station
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"Station {n + 1}")
    latitude = factory.Sequence(lambda n: 30.0 + n * 0.01)
    longitude = factory.Sequence(lambda n: 31.0 + n * 0.01)


class TrainFactory(DjangoModelFactory):
    class Meta:
        model = Train
        django_get_or_create = ("train_number",)

    train_number = factory.Sequence(lambda n: f"TRN{n + 1:04d}")
    line = factory.SubFactory(LineFactory)
    status = TrainStatus.IN_SERVICE
    has_ac = True
    direction = Direction.HELWAN
    current_station = factory.SubFactory(StationFactory)
    next_station = factory.SubFactory(StationFactory)
    camera_car_number = None


class TrainCarFactory(DjangoModelFactory):
    """Extra car beyond the ``CARS_PER_TRAIN`` that the Train post_save signal
    creates automatically — car numbers start past that range to avoid clashing
    with the auto-created ``(train, car_number)`` rows."""

    class Meta:
        model = TrainCar
        django_get_or_create = ("train", "car_number")

    train = factory.SubFactory(TrainFactory)
    car_number = factory.Sequence(lambda n: CARS_PER_TRAIN + n + 1)
    has_camera = False
    current_passengers = 0
    crowd_level = CrowdLevel.EMPTY


class ScheduleFactory(DjangoModelFactory):
    class Meta:
        model = Schedule

    train = factory.SubFactory(TrainFactory)
    station = factory.SubFactory(StationFactory)
    arrival_time = factory.LazyFunction(lambda: timezone.now() + timedelta(minutes=15))
    departure_time = factory.LazyFunction(lambda: timezone.now() + timedelta(minutes=17))
    status = TrainStatus.IN_SERVICE
