# apps/dashboard/constants/metrics_choices.py
from django.utils.translation import gettext_lazy as _
from typing import List, Tuple

# Define ALERT_LEVEL_CHOICES
ALERT_LEVEL_CHOICES = [
    ('info', _('Information')),
    ('warning', _('Warning')),
    ('critical', _('Critical')),
    ('emergency', _('Emergency'))
]

# Define REPORT_TYPE_CHOICES
REPORT_TYPE_CHOICES = [
    ('daily_passenger', _('Daily Passenger Report')),
    ('monthly_revenue', _('Monthly Revenue Report')),
    ('line_performance', _('Line Performance Report')),
    ('system_health', _('System Health Report'))
]

# Define METRIC_AGGREGATION_TYPES
METRIC_AGGREGATION_TYPES = [
    ('sum', _('Sum')),
    ('avg', _('Average')),
    ('max', _('Maximum')),
    ('min', _('Minimum'))
]


class BaseChoices:
    """
    Base class for creating choice sets with enhanced functionality
    """
    @classmethod
    def get_choices(cls) -> List[Tuple[str, str]]:
        """
        Generate choices from class attributes
        """
        return [
            (getattr(cls, attr), _(attr.replace('_', ' ').title()))
            for attr in dir(cls)
            if not attr.startswith('_') and attr.isupper()
        ]

    @classmethod
    def get_values(cls) -> List[str]:
        """
        Get all possible values
        """
        return [
            getattr(cls, attr)
            for attr in dir(cls)
            if not attr.startswith('_') and attr.isupper()
        ]


class MetricCategories(BaseChoices):
    """
    Comprehensive metric categories with enhanced functionality
    """
    REVENUE = 'REVENUE'
    PASSENGER = 'PASSENGER'
    TRAIN_PERFORMANCE = 'TRAIN_PERFORMANCE'
    OPERATIONAL = 'OPERATIONAL'
    CUSTOMER_SATISFACTION = 'CUSTOMER_SATISFACTION'

    CHOICES = [
        (REVENUE, _('Revenue Metrics')),
        (PASSENGER, _('Passenger Metrics')),
        (TRAIN_PERFORMANCE, _('Train Performance Metrics')),
        (OPERATIONAL, _('Operational Metrics')),
        (CUSTOMER_SATISFACTION, _('Customer Satisfaction Metrics'))
    ]

    @classmethod
    def get_category_description(cls, category: str) -> str:
        """
        Get detailed description for a metric category
        """
        descriptions = {
            cls.REVENUE: _('Metrics related to financial performance and income'),
            cls.PASSENGER: _('Metrics tracking passenger movement and usage'),
            cls.TRAIN_PERFORMANCE: _('Metrics measuring train operational efficiency'),
            cls.OPERATIONAL: _('Metrics related to overall system operations'),
            cls.CUSTOMER_SATISFACTION: _('Metrics measuring customer experience')
        }
        return descriptions.get(category, _('Undefined Category'))


class ReportFrequency(BaseChoices):
    """
    Enhanced report frequency with additional methods
    """
    DAILY = 'DAILY'
    WEEKLY = 'WEEKLY'
    MONTHLY = 'MONTHLY'
    QUARTERLY = 'QUARTERLY'
    ANNUAL = 'ANNUAL'

    CHOICES = [
        (DAILY, _('Daily')),
        (WEEKLY, _('Weekly')),
        (MONTHLY, _('Monthly')),
        (QUARTERLY, _('Quarterly')),
        (ANNUAL, _('Annual'))
    ]

    @classmethod
    def get_frequency_days(cls, frequency: str) -> int:
        """
        Get number of days for each frequency
        """
        frequency_days = {
            cls.DAILY: 1,
            cls.WEEKLY: 7,
            cls.MONTHLY: 30,
            cls.QUARTERLY: 90,
            cls.ANNUAL: 365
        }
        return frequency_days.get(frequency, 1)


class AlertLevels(BaseChoices):
    """
    Comprehensive alert levels with priority and color mapping
    """
    INFO = 'info'
    WARNING = 'warning'
    CRITICAL = 'critical'
    EMERGENCY = 'emergency'

    CHOICES = [
        (INFO, _('Information')),
        (WARNING, _('Warning')),
        (CRITICAL, _('Critical')),
        (EMERGENCY, _('Emergency'))
    ]

    @classmethod
    def get_priority(cls, level: str) -> int:
        """
        Get priority level for alerts
        """
        priority_map = {
            cls.INFO: 1,
            cls.WARNING: 2,
            cls.CRITICAL: 3,
            cls.EMERGENCY: 4
        }
        return priority_map.get(level, 1)

    @classmethod
    def get_color_code(cls, level: str) -> str:
        """
        Get color code for alert levels
        """
        color_map = {
            cls.INFO: '#3498db',      # Blue
            cls.WARNING: '#f39c12',   # Orange
            cls.CRITICAL: '#e74c3c',  # Red
            cls.EMERGENCY: '#8e44ad'  # Purple
        }
        return color_map.get(level, '#3498db')


class ReportTypes(BaseChoices):
    """
    Comprehensive report types with additional metadata
    """
    DAILY_PASSENGER = 'daily_passenger'
    MONTHLY_REVENUE = 'monthly_revenue'
    LINE_PERFORMANCE = 'line_performance'
    SYSTEM_HEALTH = 'system_health'
    CUSTOMER_FEEDBACK = 'customer_feedback'

    CHOICES = [
        (DAILY_PASSENGER, _('Daily Passenger Report')),
        (MONTHLY_REVENUE, _('Monthly Revenue Report')),
        (LINE_PERFORMANCE, _('Line Performance Report')),
        (SYSTEM_HEALTH, _('System Health Report')),
        (CUSTOMER_FEEDBACK, _('Customer Feedback Report'))
    ]

    @classmethod
    def get_report_details(cls, report_type: str) -> dict:
        """
        Get detailed information about report types
        """
        report_details = {
            cls.DAILY_PASSENGER: {
                'description': _('Detailed report of daily passenger movements'),
                'recommended_frequency': ReportFrequency.DAILY,
                'required_permissions': ['view_passenger_metrics']
            },
            cls.MONTHLY_REVENUE: {
                'description': _('Comprehensive monthly revenue analysis'),
                'recommended_frequency': ReportFrequency.MONTHLY,
                'required_permissions': ['view_revenue_metrics']
            },
            # Add more report type details
        }
        return report_details.get(report_type, {})


class MetricAggregationTypes(BaseChoices):
    """
    Metric aggregation types with computational details
    """
    SUM = 'sum'
    AVERAGE = 'avg'
    MAXIMUM = 'max'
    MINIMUM = 'min'
    MEDIAN = 'median'

    CHOICES = [
        (SUM, _('Sum')),
        (AVERAGE, _('Average')),
        (MAXIMUM, _('Maximum')),
        (MINIMUM, _('Minimum')),
        (MEDIAN, _('Median'))
    ]

    @classmethod
    def get_aggregation_function(cls):
        """
        Mapping to actual aggregation functions
        """
        from django.db.models import Sum, Avg, Max, Min

        aggregation_map = {
            cls.SUM: Sum,
            cls.AVERAGE: Avg,
            cls.MAXIMUM: Max,
            cls.MINIMUM: Min
        }
        return aggregation_map


# Convenience imports
METRIC_CATEGORIES = MetricCategories.get_choices()
REPORT_FREQUENCIES = ReportFrequency.get_choices()
ALERT_LEVELS = AlertLevels.get_choices()
REPORT_TYPES = ReportTypes.get_choices()
METRIC_AGGREGATION_TYPES = MetricAggregationTypes.get_choices()
