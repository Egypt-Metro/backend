from typing import Tuple
from ..constants.pricing import TicketPricing, SubscriptionPricing


def calculate_ticket_price(stations_count: int) -> Tuple[float, str]:
    """Calculate ticket price and category based on number of stations"""
    for limit, price in sorted(TicketPricing.STATION_PRICES.items()):
        if stations_count <= limit:
            return price, f'{limit}_STATIONS'
    max_limit = max(TicketPricing.STATION_PRICES.keys())
    return TicketPricing.STATION_PRICES[max_limit], f'{max_limit}_STATIONS'


def calculate_subscription_price(subscription_type: str, zones: int) -> float:
    """Calculate subscription price based on type and zones"""
    if subscription_type == 'MONTHLY':
        pricing = SubscriptionPricing.MONTHLY
    elif subscription_type == 'QUARTERLY':
        pricing = SubscriptionPricing.QUARTERLY
    else:
        return SubscriptionPricing.ANNUAL['ALL_LINES']

    return pricing.get(zones, max(pricing.values()))
