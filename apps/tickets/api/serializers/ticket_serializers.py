from rest_framework import serializers
from ...models.ticket import Ticket
from apps.stations.serializers import StationSerializer


class TicketSerializer(serializers.ModelSerializer):
    qr_code_url = serializers.SerializerMethodField()
    entry_station_details = StationSerializer(source='entry_station', read_only=True)
    exit_station_details = StationSerializer(source='exit_station', read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'ticket_number',
            'status',
            'price',
            'price_category',
            'entry_station',
            'entry_station_details',
            'exit_station',
            'exit_station_details',
            'entry_time',
            'exit_time',
            'qr_code_url',
            'valid_until',
            'created_at'
        ]
        read_only_fields = [
            'ticket_number',
            'status',
            'price',
            'qr_code_url',
            'entry_time',
            'exit_time',
            'valid_until',
            'created_at'
        ]

    def get_qr_code_url(self, obj):
        """Convert stored base64 QR code to data URL"""
        if obj.qr_code:
            return f"data:image/png;base64,{obj.qr_code}"
        return None


class TicketValidationSerializer(serializers.Serializer):
    station_id = serializers.IntegerField(required=True)
    is_entry = serializers.BooleanField(required=True)
