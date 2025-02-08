# apps/routes/serializers.py

from rest_framework import serializers


class RouteRequestSerializer(serializers.Serializer):
    start_station_id = serializers.IntegerField()
    end_station_id = serializers.IntegerField()

    def validate(self, data):
        if data["start_station_id"] == data["end_station_id"]:
            raise serializers.ValidationError("Start and end stations cannot be the same.")
        return data
