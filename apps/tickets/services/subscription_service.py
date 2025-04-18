from datetime import timedelta
from typing import Dict, List, Optional
from django.utils import timezone
from django.db import transaction
from ..models import Subscription
from ..constants.pricing import SubscriptionPricing, ZONE_STATIONS


class SubscriptionService:
    @transaction.atomic
    def create_subscription(
        self,
        user,
        subscription_type: str,
        zones_count: int,
        payment_confirmed: bool = False
    ) -> Subscription:
        """Creates a new subscription"""
        if not payment_confirmed:
            raise ValueError("Payment must be confirmed")

        # Calculate validity period
        start_date = timezone.now().date()
        if subscription_type == 'MONTHLY':
            end_date = start_date + timedelta(days=30)
            pricing = SubscriptionPricing.MONTHLY
        elif subscription_type == 'QUARTERLY':
            end_date = start_date + timedelta(days=90)
            pricing = SubscriptionPricing.QUARTERLY
        else:  # ANNUAL
            end_date = start_date + timedelta(days=365)
            pricing = SubscriptionPricing.ANNUAL['ALL_LINES']

        # Calculate price
        price = pricing.get(zones_count, max(pricing.values()))

        # Get covered zones
        covered_zones = self._get_covered_zones(zones_count)

        # Deactivate existing subscriptions
        Subscription.objects.filter(
            user=user,
            is_active=True
        ).update(is_active=False)

        # Create new subscription
        subscription = Subscription.objects.create(
            user=user,
            subscription_type=subscription_type,
            zones_count=zones_count,
            price=price,
            start_date=start_date,
            end_date=end_date,
            covered_zones=covered_zones
        )

        return subscription

    def validate_subscription(
        self,
        user,
        station_name: str
    ) -> Dict:
        """Validates if a user's subscription covers the given station"""
        active_sub = Subscription.objects.filter(
            user=user,
            is_active=True,
            end_date__gte=timezone.now().date()
        ).first()

        if not active_sub:
            return {
                'valid': False,
                'message': 'No active subscription'
            }

        # Find station's zone
        station_zone = self._get_station_zone(station_name)
        if not station_zone:
            return {
                'valid': False,
                'message': 'Invalid station'
            }

        # Check if zone is covered
        if station_zone in active_sub.covered_zones:
            return {
                'valid': True,
                'message': 'Valid subscription'
            }

        return {
            'valid': False,
            'message': 'Station not covered by subscription'
        }

    @staticmethod
    def _get_covered_zones(zones_count: int) -> List[int]:
        """Returns list of zone numbers covered by subscription"""
        return list(range(1, zones_count + 1))

    @staticmethod
    def _get_station_zone(station_name: str) -> Optional[int]:
        """Returns the zone number for a given station"""
        for zone_num, stations in ZONE_STATIONS.items():
            if station_name in stations:
                return zone_num
        return None
