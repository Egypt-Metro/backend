# apps/trains/api/filters.py

from django_filters import rest_framework as filters
from ..models.train import Train
from ..constants.choices import TrainStatus, Direction


class TrainFilter(filters.FilterSet):
    line = filters.CharFilter(field_name='line__name', lookup_expr='iexact')
    status = filters.ChoiceFilter(choices=TrainStatus.choices)
    direction = filters.ChoiceFilter(choices=Direction.choices)
    has_ac = filters.BooleanFilter()
    current_station = filters.CharFilter(
        field_name='current_station__name',
        lookup_expr='iexact'
    )
    has_camera = filters.BooleanFilter(method='filter_has_camera')
    crowd_level = filters.CharFilter(method='filter_crowd_level')

    class Meta:
        model = Train
        fields = ['line', 'status', 'direction', 'has_ac', 'current_station']

    def filter_has_camera(self, queryset, name, value):
        return queryset.filter(camera_car_number__isnull=not value)

    def filter_crowd_level(self, queryset, name, value):
        return queryset.filter(cars__crowd_level=value).distinct()
