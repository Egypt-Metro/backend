# apps/dashboard/admin.py
from django.contrib import admin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .models import AdminMetrics, RevenueMetrics, SystemAlert, ReportGeneration
import logging

logger = logging.getLogger('django.request')


@admin.register(AdminMetrics)
class AdminMetricsAdmin(admin.ModelAdmin):
    """
    Customized admin interface for AdminMetrics
    """
    list_display = (
        'id',  # Unique identifier
        'date',
        'metric_type',
        'total_passengers',
        'total_revenue'
    )
    list_filter = ('metric_type', 'date')
    search_fields = ('date', 'metric_type')

    def get_queryset(self, request):
        """
        Optimize queryset for performance
        """
        return super().get_queryset(request).select_related()

    def has_delete_permission(self, request, obj=None):
        """
        Restrict deletion of metrics
        """
        return request.user.is_superuser

    def has_add_permission(self, request):
        """
        Restrict adding metrics manually
        """
        return request.user.is_superuser


@admin.register(SystemAlert)
class SystemAlertAdmin(admin.ModelAdmin):
    """
    Advanced system alert management in admin
    """
    list_display = (
        'id',
        'title',
        'level',
        'created_at',
        'is_resolved',
        'resolved_at'
    )
    list_filter = ('level', 'is_resolved', 'created_at')
    search_fields = ('title', 'description')
    actions = ['resolve_alerts']

    def resolve_alerts(self, request, queryset):
        """
        Bulk resolve system alerts
        """
        updated_count = queryset.update(
            is_resolved=True,
            resolved_at=timezone.now()
        )

        # Log the action
        logger.info(
            f"User {request.user.username} resolved {updated_count} system alerts"
        )

        self.message_user(
            request,
            _(f'{updated_count} alerts resolved successfully')
        )
    resolve_alerts.short_description = _('Resolve Selected Alerts')

    def has_delete_permission(self, request, obj=None):
        """
        Restrict deletion of alerts
        """
        return request.user.is_superuser


@admin.register(ReportGeneration)
class ReportGenerationAdmin(admin.ModelAdmin):
    """
    Report generation management
    """
    list_display = (
        'id',
        'report_type',
        'start_date',
        'end_date',
        'generated_at',
        'generated_by'
    )
    list_filter = ('report_type', 'generated_at')
    search_fields = ('report_type', 'generated_by__username')

    def has_delete_permission(self, request, obj=None):
        """
        Restrict deletion of reports
        """
        return request.user.is_superuser


@admin.register(RevenueMetrics)
class RevenueMetricsAdmin(admin.ModelAdmin):
    """
    Admin interface for Revenue Metrics
    """
    list_display = (
        'id',  # Fixed: Added comma after 'id'
        'line',
        'date',
        'period_type',
        'total_revenue',
        'ticket_sales',
        'subscription_revenue',
        'subscription_count'
    )
    list_filter = ('line', 'period_type', 'date')
    search_fields = ('line__name',)

    def has_delete_permission(self, request, obj=None):
        """
        Restrict deletion of revenue metrics
        """
        return request.user.is_superuser

    def get_readonly_fields(self, request, obj=None):
        """
        Make certain fields read-only after creation
        """
        if obj:  # editing an existing object
            return ['line', 'date', 'period_type']
        return []

    def display_line_name(self, obj):
        """
        Custom method to display line name
        """
        return obj.line.name if obj.line else '-'
    display_line_name.short_description = 'Line'
    display_line_name.admin_order_field = 'line__name'
