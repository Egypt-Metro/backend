# apps/trains/api/filters.py

from django_filters import rest_framework as filters
from ..models import Train


class TrainFilter(filters.FilterSet):
    line = filters.CharFilter(field_name='line__name', lookup_expr='icontains')
    status = filters.CharFilter(field_name='status')
    has_ac = filters.BooleanFilter(field_name='has_air_conditioning')

    class Meta:
        model = Train
        fields = ['line', 'status', 'has_ac']
