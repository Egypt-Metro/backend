# apps/dashboard/constants/report_types.py

from django.utils.translation import gettext_lazy as _

REPORT_TYPES = [
    ('daily_passenger', _('Daily Passenger Report')),
    ('monthly_revenue', _('Monthly Revenue Report')),
    ('line_performance', _('Line Performance Report')),
    ('system_health', _('System Health Report'))
]

REPORT_FORMATS = [
    ('xlsx', _('Excel')),
    ('csv', _('CSV')),
    ('pdf', _('PDF'))
]

AGGREGATION_TYPES = [
    ('sum', _('Sum')),
    ('avg', _('Average')),
    ('max', _('Maximum')),
    ('min', _('Minimum'))
]
