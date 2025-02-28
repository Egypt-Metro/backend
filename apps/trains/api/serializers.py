# apps/trains/api/serializers.py

from rest_framework import serializers
from ..models import Train, Schedule, TrainCar, CrowdMeasurement


class CrowdLevelSerializer(serializers.ModelSerializer):
    """Serializer for crowd level information."""

    class Meta:
        model = CrowdMeasurement
        fields = [
            'id',
            'passenger_count',
            'crowd_percentage',
            'confidence_score',
            'measurement_method',
            'timestamp'
        ]


class TrainCarSerializer(serializers.ModelSerializer):
    """Serializer for train car information."""

    crowd_level = serializers.SerializerMethodField()

    class Meta:
        model = TrainCar
        fields = [
            'car_number',
            'capacity',
            'current_load',
            'crowd_status',
            'load_percentage',
            'is_operational',
            'crowd_level'
        ]

    def get_crowd_level(self, obj):
        return {
            'level': obj.crowd_status,
            'percentage': obj.load_percentage,
            'available_seats': max(0, obj.capacity - obj.current_load)
        }


class ScheduleSerializer(serializers.ModelSerializer):
    """Serializer for train schedules with computed fields."""

    station_name = serializers.CharField(source='station.name', read_only=True)
    train_id = serializers.CharField(source='train.train_id', read_only=True)
    delay_duration = serializers.IntegerField(read_only=True)
    line_name = serializers.CharField(source='train.line.name', read_only=True)

    class Meta:
        model = Schedule
        fields = [
            'id',
            'train_id',
            'station_name',
            'line_name',
            'arrival_time',
            'status',
            'expected_crowd_level',
            'is_active',
            'delay_duration',
        ]
        read_only_fields = ['delay_duration', 'is_active']

    def to_representation(self, instance):
        """Add computed fields to the representation"""
        data = super().to_representation(instance)
        data['is_delayed'] = instance.is_delayed
        data['is_cancelled'] = instance.is_cancelled
        return data


class TrainSerializer(serializers.ModelSerializer):
    """Serializer for train information."""

    cars = TrainCarSerializer(many=True, read_only=True)
    line_name = serializers.CharField(source='line.name', read_only=True)
    current_station_name = serializers.CharField(source='current_station.name', read_only=True)
    next_station_name = serializers.CharField(source='next_station.name', read_only=True)

    class Meta:
        model = Train
        fields = [
            'id',
            'train_id',
            'line_name',
            'status',
            'has_air_conditioning',
            'current_station_name',
            'next_station_name',
            'direction',
            'speed',
            'cars',
            'last_updated'
        ]


class TrainDetailSerializer(serializers.ModelSerializer):
    """Detailed train serializer including schedules and crowd information."""

    cars = TrainCarSerializer(many=True, read_only=True)
    schedules = ScheduleSerializer(many=True, read_only=True)
    line_name = serializers.CharField(source='line.name', read_only=True)
    current_station_name = serializers.CharField(source='current_station.name', read_only=True)
    next_station_name = serializers.CharField(source='next_station.name', read_only=True)
    crowd_measurements = CrowdLevelSerializer(many=True, read_only=True)

    class Meta:
        model = Train
        fields = [
            'id',
            'train_id',
            'line_name',
            'status',
            'has_air_conditioning',
            'current_station_name',
            'next_station_name',
            'direction',
            'speed',
            'cars',
            'schedules',
            'crowd_measurements',
            'last_updated'
        ]

    def to_representation(self, instance):
        """Add additional computed fields to the representation."""
        data = super().to_representation(instance)

        # Add real-time information
        data['is_delayed'] = instance.status == 'DELAYED'
        data['is_operational'] = instance.status in ['IN_SERVICE', 'DELAYED']

        # Add crowd summary
        cars_data = data.get('cars', [])
        if cars_data:
            total_load = sum(car['current_load'] for car in cars_data)
            total_capacity = sum(car['capacity'] for car in cars_data)
            data['total_passengers'] = total_load
            data['occupancy_percentage'] = round((total_load / total_capacity) * 100, 1) if total_capacity else 0

        return data


class CrowdSummarySerializer(serializers.Serializer):
    """Serializer for crowd summary information."""

    train_id = serializers.IntegerField()
    crowd_data = serializers.ListField(child=serializers.DictField())
    is_ac = serializers.BooleanField()
