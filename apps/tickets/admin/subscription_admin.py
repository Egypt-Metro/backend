# admin/subscription_admin.py
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from rangefilter.filters import DateRangeFilter  # Add this import
from ..models.subscription import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'subscription_type',
        'zones_count',
        'price',
        'status_with_days',
        'start_date',
        'end_date',
        'is_active'
    ]
    list_filter = [
        'subscription_type',
        'zones_count',
        'is_active',
        ('start_date', DateRangeFilter),
        ('end_date', DateRangeFilter)
    ]
    search_fields = [
        'user__username',
        'user__email',
        'subscription_type'
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
        'days_remaining'
    ]
    raw_id_fields = ['user']
    date_hierarchy = 'start_date'
    list_per_page = 20

    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Subscription Details', {
            'fields': (
                'subscription_type',
                'zones_count',
                'price',
                'covered_zones'
            )
        }),
        ('Validity', {
            'fields': (
                'start_date',
                'end_date',
                'is_active',
                'days_remaining'
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )

    def days_remaining(self, obj):
        """Calculate remaining days in subscription"""
        if obj.is_active and obj.end_date:
            today = timezone.now().date()
            if today <= obj.end_date:
                days = (obj.end_date - today).days
                return f"{days} days"
        return "Expired"
    days_remaining.short_description = 'Days Remaining'

    def status_with_days(self, obj):
        """Display status with remaining days"""
        if not obj.is_active:
            return format_html(
                '<span style="color: red;">Inactive</span>'
            )

        days = (obj.end_date - timezone.now().date()).days
        if days < 0:
            return format_html(
                '<span style="color: red;">Expired</span>'
            )
        elif days < 7:
            return format_html(
                '<span style="color: orange;">Active ({} days)</span>',
                days
            )
        return format_html(
            '<span style="color: green;">Active ({} days)</span>',
            days
        )
    status_with_days.short_description = 'Status'

    def save_model(self, request, obj, form, change):
        """Handle subscription creation/update"""
        if not change:  # Only for new subscriptions
            # Deactivate existing active subscriptions
            Subscription.objects.filter(
                user=obj.user,
                is_active=True
            ).update(is_active=False)
        super().save_model(request, obj, form, change)
