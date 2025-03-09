# apps/trains/api/serializers/train_serializer.py

from rest_framework import serializers
from ...models.train import Train, TrainCar


class TrainCarSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainCar
        fields = ['car_number', 'has_camera', 'current_passengers', 'crowd_level']


class TrainSerializer(serializers.ModelSerializer):
    line_name = serializers.CharField(source='line.name', read_only=True)
    current_station_name = serializers.CharField(source='current_station.name', read_only=True)
    next_station_name = serializers.CharField(source='next_station.name', read_only=True)

    class Meta:
        model = Train
        fields = [
            'id', 'train_number', 'line_name', 'status', 'has_ac',
            'direction', 'current_station_name', 'next_station_name',
            'camera_car_number'
        ]


class TrainDetailSerializer(TrainSerializer):
    cars = TrainCarSerializer(many=True, read_only=True)

    class Meta(TrainSerializer.Meta):
        fields = TrainSerializer.Meta.fields + ['cars']
