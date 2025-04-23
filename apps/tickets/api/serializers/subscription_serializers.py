# apps/tickets/api/serializers/subscription_serializers.py
from rest_framework import serializers
from django.utils import timezone
from ...models.subscription import UserSubscription, SubscriptionPlan
from ...constants.pricing import ZONE_STATIONS


class BaseSubscriptionSerializer(serializers.ModelSerializer):
    """Base serializer with common subscription fields"""
    subscription_type = serializers.CharField(source='plan.type', read_only=True)
    subscription_type_display = serializers.SerializerMethodField()
    zones_count = serializers.SerializerMethodField()
    price = serializers.DecimalField(source='plan.price', max_digits=10, decimal_places=2, read_only=True)
    days_remaining = serializers.SerializerMethodField()
    covered_zones = serializers.SerializerMethodField()
    covered_stations = serializers.SerializerMethodField()

    class Meta:
        model = UserSubscription
        fields = [
            'id',
            'subscription_type',
            'subscription_type_display',
            'zones_count',
            'price',
            'start_date',
            'end_date',
            'is_active',
            'status',
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

    def get_subscription_type_display(self, obj):
        """Get display name for subscription type"""
        subscription_types = dict(SubscriptionPlan.SUBSCRIPTION_TYPE_CHOICES)
        return subscription_types.get(obj.plan.type, '')

    def get_zones_count(self, obj):
        """Get zones count from plan"""
        if obj.plan.zones:
            return obj.plan.zones
        elif obj.plan.type == 'ANNUAL':
            # For annual plans, count is based on lines
            lines = obj.plan.lines or []
            return 2 if len(lines) <= 2 else 3  # 2 for Lines 1&2, 3 for all lines
        return None

    def get_days_remaining(self, obj):
        """Get days remaining for active subscription"""
        if obj.is_active and obj.end_date:
            today = timezone.now().date()
            if today <= obj.end_date:
                return (obj.end_date - today).days
        return 0

    def get_covered_zones(self, obj):
        """Get zones covered by the subscription"""
        if obj.plan.zones:
            # For monthly/quarterly, zones are numeric
            return list(range(1, obj.plan.zones + 1))
        elif obj.plan.type == 'ANNUAL':
            # For annual, cover all zones connected to the lines in the plan
            lines = obj.plan.lines or []
            if any('Third Line' in line for line in lines):
                # All lines cover all zones
                return list(range(1, 11))
            else:
                # Lines 1 & 2 cover zones 1-9
                return list(range(1, 10))
        return []

    def get_covered_stations(self, obj):
        """Returns list of station names covered by subscription"""
        stations = []
        covered_zones = self.get_covered_zones(obj)
        for zone in covered_zones:
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


class SubscriptionCreateSerializer(serializers.Serializer):
    """Serializer for creating new subscriptions"""
    subscription_type = serializers.ChoiceField(choices=SubscriptionPlan.SUBSCRIPTION_TYPE_CHOICES)
    zones_count = serializers.IntegerField(min_value=1, max_value=6)
    payment_confirmation = serializers.BooleanField(write_only=True)
    start_station_id = serializers.IntegerField(required=False, allow_null=True)
    end_station_id = serializers.IntegerField(required=False, allow_null=True)

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
