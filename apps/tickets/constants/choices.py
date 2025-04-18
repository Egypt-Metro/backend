# constants/choices.py

class TicketChoices:
    STATUS = [
        ('ACTIVE', 'Active'),
        ('IN_USE', 'In Use'),
        ('USED', 'Used'),
        ('USED_UPGRADED', 'Used and Upgraded'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
    ]

    TICKET_COLORS = [
        ('YELLOW', 'Yellow'),
        ('GREEN', 'Green'),
        ('RED', 'Red'),
        ('BLUE', 'Blue'),
    ]

    PRICE_CATEGORIES = [
        ('9_STATIONS', 'Up to 9 Stations'),
        ('16_STATIONS', 'Up to 16 Stations'),
        ('23_STATIONS', 'Up to 23 Stations'),
        ('39_STATIONS', 'Up to 39 Stations'),
    ]

    # Ticket Types with all details
    TICKET_TYPES = {
        'BASIC': {
            'name': 'Basic Ticket',
            'max_stations': 9,
            'price': 8,
            'color': 'YELLOW',
            'description': 'Up to 9 stations'
        },
        'STANDARD': {
            'name': 'Standard Ticket',
            'max_stations': 16,
            'price': 10,
            'color': 'GREEN',
            'description': 'Up to 16 stations'
        },
        'PREMIUM': {
            'name': 'Premium Ticket',
            'max_stations': 23,
            'price': 15,
            'color': 'RED',
            'description': 'Up to 23 stations'
        },
        'VIP': {
            'name': 'VIP Ticket',
            'max_stations': 39,
            'price': 20,
            'color': 'BLUE',
            'description': 'Up to 39 stations'
        }
    }

    @classmethod
    def get_next_ticket_type(cls, stations_count: int) -> tuple:
        """
        Get next appropriate ticket type for stations count
        Returns (ticket_type, details) tuple
        """
        sorted_tickets = sorted(
            cls.TICKET_TYPES.items(),
            key=lambda x: x[1]['max_stations']
        )

        for ticket_type, details in sorted_tickets:
            if details['max_stations'] >= stations_count:
                return ticket_type, details
        return 'VIP', cls.TICKET_TYPES['VIP']

    @classmethod
    def get_ticket_type_choices(cls):
        """Get choices for ticket types"""
        return [(k, v['name']) for k, v in cls.TICKET_TYPES.items()]


class SubscriptionChoices:
    TYPES = [
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('ANNUAL', 'Annual'),
    ]

    ZONES = [(i, f'{i} Zone{"s" if i > 1 else ""}') for i in range(1, 7)]
