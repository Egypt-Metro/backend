from rest_framework import serializers
from django.utils import timezone
from ...models.subscription import Subscription
from ...constants.pricing import ZONE_STATIONS


class BaseSubscriptionSerializer(serializers.ModelSerializer):
    """Base serializer with common subscription fields"""
    subscription_type_display = serializers.CharField(
        source='get_subscription_type_display',
        read_only=True
    )
    days_remaining = serializers.SerializerMethodField()
    covered_stations = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = [
            'id',
            'subscription_type',
            'subscription_type_display',
            'zones_count',
            'price',
            'start_date',
            'end_date',
            'is_active',
            'covered_zones',
            'covered_stations',
            'days_remaining',
            'created_at'
        ]
        read_only_fields = [
            'price',
            'is_active',
            'covered_zones',
            'created_at'
        ]

    def get_days_remaining(self, obj):
        if obj.is_active and obj.end_date:
            today = timezone.now().date()
            if today <= obj.end_date:
                return (obj.end_date - today).days
        return 0

    def get_covered_stations(self, obj):
        """Returns list of station names covered by subscription"""
        stations = []
        for zone in obj.covered_zones:
            if zone in ZONE_STATIONS:
                stations.extend(ZONE_STATIONS[zone])
        return sorted(stations)


class SubscriptionListSerializer(BaseSubscriptionSerializer):
    """Serializer for listing subscriptions with minimal fields"""
    class Meta(BaseSubscriptionSerializer.Meta):
        fields = [
            'id',
            'subscription_type_display',
            'zones_count',
            'is_active',
            'end_date',
            'days_remaining'
        ]


class SubscriptionDetailSerializer(BaseSubscriptionSerializer):
    """Serializer for detailed subscription view"""
    pass


class SubscriptionCreateSerializer(BaseSubscriptionSerializer):
    """Serializer for creating new subscriptions"""
    payment_confirmation = serializers.BooleanField(write_only=True)

    class Meta(BaseSubscriptionSerializer.Meta):
        fields = BaseSubscriptionSerializer.Meta.fields + ['payment_confirmation']

    def validate(self, data):
        """Validate subscription data"""
        subscription_type = data['subscription_type']
        zones_count = data['zones_count']

        # Validate zones count based on subscription type
        if subscription_type == 'ANNUAL':
            if zones_count not in [2, 3]:  # 2 for Lines 1&2, 3 for all lines
                raise serializers.ValidationError({
                    'zones_count': 'Annual subscriptions must cover either 2 lines or all lines'
                })
        elif zones_count > 6:
            raise serializers.ValidationError({
                'zones_count': 'Monthly and Quarterly subscriptions can cover up to 6 zones'
            })

        return data


class SubscriptionValidationSerializer(serializers.Serializer):
    """Serializer for subscription validation requests"""
    station_name = serializers.CharField(
        max_length=100,
        required=True
    )

    def validate_station_name(self, value):
        """Validate station exists in zone definitions"""
        if not any(value in stations for stations in ZONE_STATIONS.values()):
            raise serializers.ValidationError('Invalid station name')
        return value
