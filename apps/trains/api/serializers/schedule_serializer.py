# apps/trains/api/serializers/schedule_serializer.py

from rest_framework import serializers
from ...models.schedule import Schedule


class ScheduleSerializer(serializers.ModelSerializer):
    train_number = serializers.CharField(source='train.train_number')
    station_name = serializers.CharField(source='station.name')
    crowd_level = serializers.SerializerMethodField()

    class Meta:
        model = Schedule
        fields = [
            'id', 'train_number', 'station_name', 'arrival_time',
            'departure_time', 'status', 'crowd_level'
        ]

    def get_crowd_level(self, obj):
        return obj.train.get_crowd_level()
