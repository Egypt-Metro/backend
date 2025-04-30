# apps/tickets/api/serializers/ticket_serializers.py

from rest_framework import serializers
from ...models.ticket import Ticket
from apps.stations.serializers import StationSerializer
from ...constants.choices import TicketChoices


class TicketSerializer(serializers.ModelSerializer):
    ticket_type = serializers.ChoiceField(
        choices=list(TicketChoices.TICKET_TYPES.keys()),
        required=True
    )
    quantity = serializers.IntegerField(
        min_value=1,
        default=1,
        required=False,
        help_text="Number of tickets to purchase"
    )
    qr_code_url = serializers.SerializerMethodField()
    entry_station_details = StationSerializer(source='entry_station', read_only=True)
    exit_station_details = StationSerializer(source='exit_station', read_only=True)
    ticket_details = serializers.SerializerMethodField()
    needs_upgrade = serializers.BooleanField(read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id',
            'ticket_number',
            'ticket_type',
            'quantity',
            'status',
            'price',
            'color',
            'max_stations',
            'entry_station_details',
            'exit_station_details',
            'entry_time',
            'exit_time',
            'needs_upgrade',
            'valid_until',
            'created_at',
            'ticket_details',
            'entry_station_id',
            'exit_station_id',
            'qr_code_url'
        ]
        read_only_fields = [
            'id',
            'ticket_number',
            'price',
            'color',
            'max_stations',
            'entry_station_details',
            'exit_station_details',
            'entry_time',
            'exit_time',
            'qr_code_url',
            'valid_until',
            'created_at',
            'ticket_details'
        ]

    def get_qr_code_url(self, obj):
        """Convert stored base64 QR code to data URL"""
        if obj.qr_code:
            return f"data:image/png;base64,{obj.qr_code}"
        return None

    def get_ticket_details(self, obj):
        """Get ticket type details"""
        ticket_type = obj.ticket_type
        details = TicketChoices.TICKET_TYPES.get(ticket_type, {})
        return {
            'name': details.get('name'),
            'max_stations': details.get('max_stations'),
            'price': details.get('price'),
            'color': details.get('color'),
            'description': details.get('description')
        }

    def validate_ticket_type(self, value):
        """Validate ticket type"""
        if value not in TicketChoices.TICKET_TYPES:
            raise serializers.ValidationError(
                f"Invalid ticket type. Must be one of {list(TicketChoices.TICKET_TYPES.keys())}"
            )
        return value

    def validate_quantity(self, value):
        """Validate quantity"""
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1")
        return value


class TicketValidationSerializer(serializers.Serializer):
    """Serializer for ticket validation at gates"""
    station_id = serializers.IntegerField(required=True)


class TicketUpgradeSerializer(serializers.Serializer):
    """Serializer for ticket upgrades"""
    new_ticket_type = serializers.ChoiceField(
        choices=list(TicketChoices.TICKET_TYPES.keys()),
        required=True
    )
    payment_confirmed = serializers.BooleanField(default=False)


class TicketListQueryParamsSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=['ACTIVE', 'IN_USE', 'USED', 'EXPIRED', 'ALL'],
        required=False
    )
