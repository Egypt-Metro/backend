# apps/dashboard/utils/validators.py

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re


class ReportValidator:
    """
    Advanced validation utilities for reports
    """
    @staticmethod
    def validate_date_range(start_date, end_date):
        """
        Validate report date range
        """
        if start_date > end_date:
            raise ValidationError(
                _('Start date must be before end date')
            )

    @staticmethod
    def validate_report_type(report_type):
        """
        Validate report type
        """
        valid_types = [
            'daily_passenger',
            'monthly_revenue',
            'line_performance'
        ]

        if report_type not in valid_types:
            raise ValidationError(
                _('Invalid report type')
            )

    @staticmethod
    def sanitize_filename(filename):
        """
        Sanitize filename to prevent security issues
        """
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)
        return sanitized[:255]  # Limit filename length
