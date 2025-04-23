# admin/subscription_admin.py
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from rangefilter.filters import DateRangeFilter
from ..models.subscription import UserSubscription, SubscriptionPlan


class IsActiveFilter(admin.SimpleListFilter):
    title = 'Active Status'
    parameter_name = 'active_status'

    def lookups(self, request, model_admin):
        return (
            ('active', 'Active'),
            ('inactive', 'Inactive')
        )

    def queryset(self, request, queryset):
        now = timezone.now().date()
        if self.value() == 'active':
            return queryset.filter(
                status='ACTIVE',
                end_date__gte=now
            )
        if self.value() == 'inactive':
            return queryset.filter(
                status__in=['EXPIRED', 'CANCELLED']
            ).union(
                queryset.filter(
                    status='ACTIVE',
                    end_date__lt=now
                )
            )


@admin.register(UserSubscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'get_subscription_type',
        'get_zones_count',
        'get_price',
        'status_with_days',
        'start_date',
        'end_date',
        'is_active'
    ]
    list_filter = [
        'plan__type',
        'status',
        IsActiveFilter,
        ('start_date', DateRangeFilter),
        ('end_date', DateRangeFilter)
    ]
    search_fields = [
        'user__username',
        'user__email',
        'plan__type'
    ]
    readonly_fields = [
        'created_at',
        'updated_at',
        'days_remaining'
    ]
    raw_id_fields = ['user', 'plan']
    date_hierarchy = 'start_date'
    list_per_page = 20

    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Subscription Details', {
            'fields': (
                'plan',
                'start_station',
                'end_station',
                'status'
            )
        }),
        ('Validity', {
            'fields': (
                'start_date',
                'end_date',
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

    def get_subscription_type(self, obj):
        return obj.plan.type
    get_subscription_type.short_description = 'Subscription Type'
    get_subscription_type.admin_order_field = 'plan__type'

    def get_zones_count(self, obj):
        if obj.plan.zones:
            return obj.plan.zones
        elif obj.plan.type == 'ANNUAL':
            lines = obj.plan.lines or []
            return 2 if len(lines) <= 2 else 3
        return None
    get_zones_count.short_description = 'Zones'

    def get_price(self, obj):
        return obj.plan.price
    get_price.short_description = 'Price'
    get_price.admin_order_field = 'plan__price'

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
        if obj.status != 'ACTIVE':
            return format_html(
                '<span style="color: red;">{}</span>',
                obj.get_status_display()
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
            UserSubscription.objects.filter(
                user=obj.user,
                status='ACTIVE'
            ).update(status='CANCELLED')
        super().save_model(request, obj, form, change)


# Register the SubscriptionPlan model as well
@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'type', 'price', 'zones', 'get_lines']
    list_filter = ['type']
    search_fields = ['name', 'description']

    def get_lines(self, obj):
        if obj.lines:
            return ", ".join(obj.lines)
        return "-"
    get_lines.short_description = 'Lines'


class IsActiveFilter(admin.SimpleListFilter):
    title = 'Active Status'
    parameter_name = 'active_status'

    def lookups(self, request, model_admin):
        return (
            ('active', 'Active'),
            ('inactive', 'Inactive')
        )

    def queryset(self, request, queryset):
        now = timezone.now().date()
        if self.value() == 'active':
            return queryset.filter(
                status='ACTIVE',
                end_date__gte=now
            )
        if self.value() == 'inactive':
            return queryset.filter(
                status__in=['EXPIRED', 'CANCELLED']
            ).union(
                queryset.filter(
                    status='ACTIVE',
                    end_date__lt=now
                )
            )
