# apps/dashboard/models.py
import os
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.conf import settings
from .constants.metrics_choices import (
    ALERT_LEVEL_CHOICES,
    REPORT_TYPE_CHOICES
)


class AdminMetrics(models.Model):
    """
    Comprehensive metro performance metrics tracking
    """
    class MetricType(models.TextChoices):
        DAILY = 'daily', _('Daily Metrics')
        WEEKLY = 'weekly', _('Weekly Metrics')
        MONTHLY = 'monthly', _('Monthly Metrics')

    date = models.DateField(_('Metric Date'), auto_now_add=True, db_index=True)
    metric_type = models.CharField(
        _('Metric Type'),
        max_length=10,
        choices=MetricType.choices,
        default=MetricType.DAILY
    )
    total_passengers = models.PositiveIntegerField(
        _('Total Passengers'),
        validators=[MinValueValidator(0)],
        help_text=_('Total number of passengers for the period')
    )
    total_revenue = models.DecimalField(
        _('Total Revenue'),
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('Total revenue generated')
    )
    line_performance = models.JSONField(
        _('Line Performance'),
        default=dict,
        help_text=_('Detailed performance metrics per metro line')
    )

    class Meta:
        verbose_name = _('Admin Metric')
        ordering = ['-date']
        unique_together = ['date', 'metric_type']


class RevenueMetrics(models.Model):
    """
    Comprehensive revenue and sales tracking
    """
    class MetricPeriod(models.TextChoices):
        DAILY = 'daily', _('Daily')
        WEEKLY = 'weekly', _('Weekly')
        MONTHLY = 'monthly', _('Monthly')
        YEARLY = 'yearly', _('Yearly')

    date = models.DateField(_('Metric Date'), auto_now_add=True, db_index=True)
    period_type = models.CharField(
        _('Period Type'),
        max_length=10,
        choices=MetricPeriod.choices,
        default=MetricPeriod.DAILY
    )

    # Line-specific metrics
    line = models.ForeignKey(
        'stations.Line',
        on_delete=models.CASCADE,
        related_name='revenue_metrics'
    )

    # Revenue metrics
    total_revenue = models.DecimalField(
        _('Total Revenue'),
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('Total revenue generated')
    )
    ticket_sales = models.PositiveIntegerField(
        _('Ticket Sales'),
        default=0,
        help_text=_('Number of tickets sold')
    )

    # Subscription metrics
    subscription_revenue = models.DecimalField(
        _('Subscription Revenue'),
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('Revenue from subscriptions')
    )
    subscription_count = models.PositiveIntegerField(
        _('Subscription Count'),
        default=0,
        help_text=_('Number of active subscriptions')
    )

    # Additional metrics
    avg_ticket_price = models.DecimalField(
        _('Average Ticket Price'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text=_('Average ticket price')
    )

    class Meta:
        verbose_name = _('Revenue Metric')
        ordering = ['-date']
        unique_together = ['date', 'line', 'period_type']
        indexes = [
            models.Index(fields=['date', 'line']),
            models.Index(fields=['period_type']),
        ]

    def __str__(self):
        return f"{self.line.name} - {self.period_type.capitalize()} Revenue ({self.date})"


class SystemAlert(models.Model):
    """
    Advanced system-wide alert management
    """
    title = models.CharField(
        _('Alert Title'),
        max_length=255,
        help_text=_('Concise alert title')
    )
    description = models.TextField(
        _('Alert Description'),
        help_text=_('Detailed alert information')
    )
    level = models.CharField(
        _('Alert Level'),
        max_length=20,
        choices=ALERT_LEVEL_CHOICES,
        default='info'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_alerts'
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True, db_index=True)
    resolved_at = models.DateTimeField(_('Resolved At'), null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='resolved_alerts'
    )
    is_resolved = models.BooleanField(_('Resolved'), default=False)

    class Meta:
        verbose_name = _('System Alert')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_resolved', 'created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.level}"


class ReportGeneration(models.Model):
    """
    Track and manage report generation processes
    """
    report_type = models.CharField(
        _('Report Type'),
        max_length=50,
        choices=REPORT_TYPE_CHOICES
    )
    start_date = models.DateField(_('Start Date'))
    end_date = models.DateField(_('End Date'))
    generated_at = models.DateTimeField(_('Generated At'), auto_now_add=True)
    file_path = models.FilePathField(
        _('Report File Path'),
        path=settings.DASHBOARD_CONFIG.get(
            'REPORT_STORAGE_PATH',
            os.path.join(os.path.dirname(__file__), 'reports')
        ),
        recursive=True,
        max_length=500,
        null=True,
        blank=True
    )
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )

    class Meta:
        verbose_name = _('Report Generation')
        ordering = ['-generated_at']

    def __str__(self):
        return f"{self.report_type} Report ({self.start_date} - {self.end_date})"

    def save(self, *args, **kwargs):
        """
        Ensure the reports directory exists
        """
        # Create reports directory if it doesn't exist
        reports_dir = settings.DASHBOARD_CONFIG.get(
            'REPORT_STORAGE_PATH',
            os.path.join(os.path.dirname(__file__), 'reports')
        )
        os.makedirs(reports_dir, exist_ok=True)

        super().save(*args, **kwargs)
