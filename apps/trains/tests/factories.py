import factory
from factory.django import DjangoModelFactory

from apps.stations.models import Line, Station
from apps.trains.models import Train, TrainCar

from ..constants import LINE_CONFIG


class LineFactory(DjangoModelFactory):
    class Meta:
        model = Line

    name = factory.Sequence(lambda n: f"Line {n}")
    color_code = factory.Sequence(lambda n: f"#FF{n:04d}")


class StationFactory(DjangoModelFactory):
    class Meta:
        model = Station

    name = factory.Sequence(lambda n: f"Station {n}")
    latitude = factory.Faker("latitude")
    longitude = factory.Faker("longitude")


class TrainFactory(DjangoModelFactory):
    class Meta:
        model = Train

    @factory.lazy_attribute
    def train_id(self):
        return f"{self.line.name}_AC_{factory.Sequence(int)}"

    line = factory.SubFactory(LineFactory)
    has_air_conditioning = True
    current_station = factory.SubFactory(StationFactory)
    next_station = factory.SubFactory(StationFactory)

    @factory.lazy_attribute
    def direction(self):
        line_name = f"LINE_{self.line.name}"
        line_config = LINE_CONFIG.get(line_name, {})
        directions = line_config.get("directions", [])
        return directions[0][0] if directions else "HELWAN"

    status = "IN_SERVICE"
    latitude = factory.Faker("latitude")
    longitude = factory.Faker("longitude")
    speed = factory.Faker("pyfloat", min_value=0, max_value=80)


class TrainCarFactory(DjangoModelFactory):
    class Meta:
        model = TrainCar

    train = factory.SubFactory(TrainFactory)
    car_number = factory.Sequence(lambda n: n + 1)
    capacity = 300
    current_load = factory.Faker("pyint", min_value=0, max_value=300)
