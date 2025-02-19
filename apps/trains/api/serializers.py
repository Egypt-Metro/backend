# apps/trains/api/serializers.py

from rest_framework import serializers

from ..models import CrowdMeasurement, Schedule, Train


class TrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Train
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["line_name"] = instance.line.name
        data["current_station_name"] = instance.current_station.name if instance.current_station else None
        return data


class ScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Schedule
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["station_name"] = instance.station.name
        data["train_id"] = instance.train.train_id
        return data


class TrainStatusSerializer(serializers.Serializer):
    train_id = serializers.CharField()
    current_location = serializers.DictField()
    speed = serializers.FloatField()
    status = serializers.CharField()
    next_station = serializers.CharField()
    estimated_arrival = serializers.DateTimeField()
    crowd_level = serializers.CharField()


class CrowdLevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrowdMeasurement
        fields = ["timestamp", "passenger_count", "crowd_percentage", "confidence_score"]


class TrainDetailSerializer(serializers.ModelSerializer):
    schedule = ScheduleSerializer(many=True, read_only=True, source="schedule_set")
    crowd_measurements = CrowdLevelSerializer(many=True, read_only=True, source="crowdmeasurement_set")

    class Meta:
        model = Train
        fields = [
            "train_id",
            "line",
            "status",
            "current_station",
            "next_station",
            "last_updated",
            "schedule",
            "crowd_measurements",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["line_name"] = instance.line.name
        data["current_station_name"] = instance.current_station.name if instance.current_station else None
        data["next_station_name"] = instance.next_station.name if instance.next_station else None
        return data
