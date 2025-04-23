from typing import Dict, Tuple

from apps.tickets.constants.pricing import SubscriptionPricing
from apps.tickets.models.subscription import StationZone, ZoneMatrix
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


class SubscriptionPriceCalculator:
    @staticmethod
    def get_zones_between(start_station, end_station):
        """Calculate zones traveled between two stations"""
        try:
            start_zone = StationZone.objects.get(station=start_station).zone_number
            end_zone = StationZone.objects.get(station=end_station).zone_number
            zone_mapping = ZoneMatrix.objects.get(
                source_zone=start_zone,
                destination_zone=end_zone
            )
            return zone_mapping.zones_crossed
        except (StationZone.DoesNotExist, ZoneMatrix.DoesNotExist):
            # Fallback to matrix in constants
            from ..constants.pricing import ZONE_MATRIX
            try:
                start_zone = str(start_zone)
                end_zone = str(end_zone)
                return ZONE_MATRIX[start_zone][end_zone]
            except (KeyError, NameError):
                raise ValueError("Could not determine zones between stations")

    @staticmethod
    def get_monthly_price(zones):
        """Get monthly subscription price based on zones"""
        if zones <= 1:
            return SubscriptionPricing.MONTHLY[1]
        elif zones == 2:
            return SubscriptionPricing.MONTHLY[2]
        elif zones <= 4:
            return SubscriptionPricing.MONTHLY[4]
        else:
            return SubscriptionPricing.MONTHLY[6]

    @staticmethod
    def get_quarterly_price(zones):
        """Get quarterly subscription price based on zones"""
        if zones <= 1:
            return SubscriptionPricing.QUARTERLY[1]
        elif zones == 2:
            return SubscriptionPricing.QUARTERLY[2]
        elif zones <= 4:
            return SubscriptionPricing.QUARTERLY[4]
        else:
            return SubscriptionPricing.QUARTERLY[6]

    @staticmethod
    def get_annual_price(lines_needed):
        """Get annual subscription price based on lines needed"""
        if all(line in ["First Line", "Second Line"] for line in lines_needed):
            return SubscriptionPricing.ANNUAL['LINES_1_2']
        return SubscriptionPricing.ANNUAL['ALL_LINES']

    @staticmethod
    def calculate_subscription_price(subscription_type, zones, lines=None):
        """Calculate subscription price based on type and zones/lines"""
        if subscription_type == 'MONTHLY':
            return SubscriptionPriceCalculator.get_monthly_price(zones)
        elif subscription_type == 'QUARTERLY':
            return SubscriptionPriceCalculator.get_quarterly_price(zones)
        else:  # ANNUAL
            if lines and all(line in ["First Line", "Second Line"] for line in lines):
                return SubscriptionPricing.ANNUAL['LINES_1_2']
            return SubscriptionPricing.ANNUAL['ALL_LINES']
