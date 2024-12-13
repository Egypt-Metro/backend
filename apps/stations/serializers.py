from rest_framework import serializers
from .models import Station, Line


class LineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Line
        fields = ["id", "name"]


class StationSerializer(serializers.ModelSerializer):
    lines = LineSerializer(many=True)  # Serialize associated lines

    class Meta:
        model = Station
        fields = ["id", "name", "lines"]
