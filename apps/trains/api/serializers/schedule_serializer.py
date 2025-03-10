# apps/trains/api/serializers/schedule_serializer.py

from rest_framework import serializers
from ...models.schedule import Schedule


class ScheduleSerializer(serializers.ModelSerializer):
    train_number = serializers.CharField(source='train.train_number')
    direction = serializers.CharField(source='train.direction')
    has_ac = serializers.BooleanField(source='train.has_ac')
    line = serializers.SerializerMethodField()
    monitored_car = serializers.SerializerMethodField()
    crowd_level = serializers.SerializerMethodField()
    passenger_count = serializers.SerializerMethodField()

    class Meta:
        model = Schedule
        fields = [
            'id', 'train_number', 'direction', 'arrival_time',
            'departure_time', 'status', 'has_ac', 'crowd_level',
            'passenger_count', 'line', 'monitored_car'
        ]

    def get_line(self, obj):
        return {
            'name': obj.train.line.name,
            'color_code': obj.train.line.color_code
        }

    def get_monitored_car(self, obj):
        if obj.train.is_monitored:
            car = obj.train.cars.get(car_number=obj.train.camera_car_number)
            return {
                'car_number': car.car_number,
                'current_passengers': car.current_passengers,
                'crowd_level': car.crowd_level
            }
        return None

    def get_crowd_level(self, obj):
        return obj.train.get_crowd_level()

    def get_passenger_count(self, obj):
        return obj.train.get_total_passengers()
