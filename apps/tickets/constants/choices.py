# constants/choices.py

class TicketChoices:
    STATUS = [
        ('PENDING', 'Pending Payment'),
        ('ACTIVE', 'Active'),
        ('IN_USE', 'In Use'),
        ('USED', 'Used'),
        ('USED_UPGRADED', 'Used and Upgraded'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
    ]

    PRICE_CATEGORIES = [
        ('9_STATIONS', 'Up to 9 Stations'),
        ('16_STATIONS', 'Up to 16 Stations'),
        ('23_STATIONS', 'Up to 23 Stations'),
        ('39_STATIONS', 'Up to 39 Stations'),
    ]


class SubscriptionChoices:
    TYPES = [
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('ANNUAL', 'Annual'),
    ]

    ZONES = [(i, f'{i} Zone{"s" if i > 1 else ""}') for i in range(1, 7)]
