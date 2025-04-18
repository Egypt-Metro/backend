from typing import Dict, Tuple
from ..constants.choices import TicketChoices


def calculate_ticket_price(stations_count: int) -> Tuple[float, str]:
    """
    Calculate ticket price and category based on number of stations
    """
    next_type, details = TicketChoices.get_next_ticket_type(stations_count)
    return details['price'], next_type


def calculate_ticket_details(stations_count: int) -> Dict:
    """Calculate ticket details based on number of stations"""
    next_type, details = TicketChoices.get_next_ticket_type(stations_count)

    return {
        'ticket_type': next_type,
        'price': details['price'],
        'max_stations': details['max_stations'],
        'color': details['color']
    }


def calculate_upgrade_details(current_type: str, stations_count: int) -> Dict:
    """Calculate upgrade details for a ticket"""
    current_config = TicketChoices.TICKET_TYPES[current_type]
    next_type, next_config = TicketChoices.get_next_ticket_type(stations_count)

    return {
        'current_type': current_type,
        'current_price': current_config['price'],
        'next_type': next_type,
        'upgrade_price': next_config['price'] - current_config['price'],
        'new_max_stations': next_config['max_stations']
    }


def calculate_subscription_price(subscription_type: str, zones: int) -> float:
    """Calculate subscription price based on type and zones"""
    from ..constants.pricing import SubscriptionPricing

    if subscription_type == 'MONTHLY':
        pricing = SubscriptionPricing.MONTHLY
    elif subscription_type == 'QUARTERLY':
        pricing = SubscriptionPricing.QUARTERLY
    else:
        return SubscriptionPricing.ANNUAL['ALL_LINES']

    return pricing.get(zones, max(pricing.values()))
