# apps/tickets/admin/subscription_admin.py
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.db.models import Q
from django.contrib import messages
from rangefilter.filters import DateRangeFilter

from ..models.subscription import UserSubscription, SubscriptionPlan


class IsActiveFilter(admin.SimpleListFilter):
    title = 'Subscription Status'
    parameter_name = 'active_status'

    def lookups(self, request, model_admin):
        return (
            ('active', 'Active'),
            ('expiring_soon', 'Expiring within 7 days'),
            ('inactive', 'Inactive'),
            ('expired', 'Expired'),
            ('cancelled', 'Cancelled'),
        )

    def queryset(self, request, queryset):
        now = timezone.now().date()

        if self.value() == 'active':
            return queryset.filter(
                status='ACTIVE',
                end_date__gte=now
            )
        if self.value() == 'expiring_soon':
            return queryset.filter(
                status='ACTIVE',
                end_date__gte=now,
                end_date__lte=now + timezone.timedelta(days=7)
            )
        if self.value() == 'inactive':
            return queryset.filter(
                Q(status__in=['EXPIRED', 'CANCELLED'])
                | Q(status='ACTIVE', end_date__lt=now)  # Line break before the | operator
            )
        if self.value() == 'expired':
            return queryset.filter(
                status='EXPIRED'
            ).union(
                queryset.filter(
                    status='ACTIVE',
                    end_date__lt=now
                )
            )
        if self.value() == 'cancelled':
            return queryset.filter(status='CANCELLED')


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    """Admin for subscription plans"""
    list_display = [
        'name',
        'type',
        'price',
        'get_zones_display',
        'get_lines_display',
        'description'
    ]

    list_filter = [
        'type',
    ]

    search_fields = [
        'name',
        'type',
        'description',
    ]

    def get_zones_display(self, obj):
        if obj.zones:
            return "{} Zone{}".format(obj.zones, 's' if obj.zones > 1 else '')
        return "-"
    get_zones_display.short_description = "Zones"

    def get_lines_display(self, obj):
        if obj.lines:
            return ", ".join(obj.lines)
        return "-"
    get_lines_display.short_description = "Lines"


@admin.register(UserSubscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'get_user_display',
        'subscription_info',
        'price_display',
        'status_with_days',
        'period_display',
    ]

    list_filter = [
        IsActiveFilter,
        ('plan__type', admin.ChoicesFieldListFilter),
        ('status', admin.ChoicesFieldListFilter),
        ('start_date', DateRangeFilter),
        ('end_date', DateRangeFilter),
    ]

    search_fields = [
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name',
        'plan__name',
        'plan__type',
    ]

    readonly_fields = [
        'created_at',
        'updated_at',
        'days_remaining',
    ]

    raw_id_fields = ['user', 'plan', 'start_station', 'end_station']
    date_hierarchy = 'start_date'
    list_per_page = 25

    actions = [
        'extend_subscription',
        'cancel_subscriptions',
        'mark_as_expired',
    ]

    fieldsets = (
        ('User Information', {
            'fields': (
                'user',
                ('start_station', 'end_station'),
            ),
        }),
        ('Subscription Details', {
            'fields': (
                'plan',
                'status',
            ),
        }),
        ('Validity Period', {
            'fields': (
                ('start_date', 'end_date'),
                'days_remaining',
            ),
        }),
        ('Metadata', {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        """Optimize queries with select_related"""
        queryset = super().get_queryset(request)
        return queryset.select_related(
            'user',
            'plan',
            'start_station',
            'end_station'
        )

    def get_user_display(self, obj):
        """Display user info without trying to link to user admin"""
        if obj.user:
            return format_html(
                '<strong>{}</strong><br/><span style="color:#999">{}</span>',
                obj.user.username, obj.user.email
            )
        return "-"
    get_user_display.short_description = 'User'
    get_user_display.admin_order_field = 'user__username'

    def subscription_info(self, obj):
        """Display subscription type and covered zones/lines"""
        if obj.plan.type == 'ANNUAL':
            lines = obj.plan.lines or []
            lines_text = ", ".join(lines) if lines else "All Lines"
            return format_html(
                '<strong>{}</strong><br/><span style="color:#666">Annual - {}</span>',
                obj.plan.name, lines_text
            )
        else:
            zones = obj.plan.zones or 0
            zones_suffix = 's' if zones > 1 else ''
            return format_html(
                '<strong>{}</strong><br/><span style="color:#666">{} - {} Zone{}</span>',
                obj.plan.name,
                obj.plan.get_type_display(),
                zones,
                zones_suffix
            )
    subscription_info.short_description = 'Subscription'
    subscription_info.admin_order_field = 'plan__type'

    def price_display(self, obj):
        """Display price with currency"""
        if obj.plan and obj.plan.price:
            # Pre-format the price value before passing to format_html
            formatted_price = "{:.2f}".format(float(obj.plan.price))
            return format_html(
                '<span style="font-weight:bold; color:#28a745;">{} EGP</span>',
                formatted_price
            )
        return "-"
    price_display.short_description = 'Price'
    price_display.admin_order_field = 'plan__price'

    def period_display(self, obj):
        """Display subscription period with calendar icons"""
        start_date = obj.start_date.strftime('%Y-%m-%d')
        end_date = obj.end_date.strftime('%Y-%m-%d')
        return format_html(
            '<span title="Start date">{}</span><br/>'
            '<span title="End date">{}</span>',
            start_date, end_date
        )
    period_display.short_description = 'Period'

    def status_with_days(self, obj):
        """Display status with remaining days in colorized format"""
        now = timezone.now().date()

        if obj.status != 'ACTIVE':
            return format_html(
                '<span style="color:red; font-weight:bold;">{}</span>',
                obj.get_status_display()
            )

        if obj.end_date < now:
            return format_html(
                '<span style="color:red; font-weight:bold;">Expired</span>'
            )

        days = (obj.end_date - now).days
        day_suffix = 's' if days != 1 else ''

        if days < 3:
            return format_html(
                '<span style="color:red; font-weight:bold;">Active</span><br/>'
                '<span style="color:red; font-size:0.8em;">{} day{} left</span>',
                days, day_suffix
            )
        elif days < 7:
            return format_html(
                '<span style="color:orange; font-weight:bold;">Active</span><br/>'
                '<span style="color:orange; font-size:0.8em;">{} days left</span>',
                days
            )
        else:
            return format_html(
                '<span style="color:green; font-weight:bold;">Active</span><br/>'
                '<span style="color:green; font-size:0.8em;">{} days left</span>',
                days
            )
    status_with_days.short_description = 'Status'

    def days_remaining(self, obj):
        """Calculate remaining days in subscription"""
        if not obj.is_active or not obj.end_date:
            return "Subscription not active"

        today = timezone.now().date()
        if today > obj.end_date:
            return format_html('<span style="color:red;">Expired</span>')

        days = (obj.end_date - today).days
        return "{} days remaining".format(days)
    days_remaining.short_description = 'Days Remaining'

    def extend_subscription(self, request, queryset):
        """Bulk action to extend selected subscriptions"""
        extended = 0
        for subscription in queryset:
            if subscription.status == 'ACTIVE':
                # Add the subscription period to the current end_date
                if subscription.plan.type == 'MONTHLY':
                    subscription.end_date = subscription.end_date + timezone.timedelta(days=30)
                elif subscription.plan.type == 'QUARTERLY':
                    subscription.end_date = subscription.end_date + timezone.timedelta(days=90)
                elif subscription.plan.type == 'ANNUAL':
                    subscription.end_date = subscription.end_date + timezone.timedelta(days=365)
                subscription.save(update_fields=['end_date', 'updated_at'])
                extended += 1

        message = "Successfully extended {} subscription(s).".format(extended)
        self.message_user(request, message, messages.SUCCESS)
    extend_subscription.short_description = "Extend selected subscriptions"

    def cancel_subscriptions(self, request, queryset):
        """Bulk action to cancel selected subscriptions"""
        cancelled = queryset.filter(status='ACTIVE').update(
            status='CANCELLED',
            updated_at=timezone.now()
        )
        message = "Successfully cancelled {} subscription(s).".format(cancelled)
        self.message_user(request, message, messages.SUCCESS)
    cancel_subscriptions.short_description = "Cancel selected subscriptions"

    def mark_as_expired(self, request, queryset):
        """Bulk action to mark selected subscriptions as expired"""
        expired = queryset.filter(status='ACTIVE').update(
            status='EXPIRED',
            updated_at=timezone.now()
        )
        message = "Marked {} subscription(s) as expired.".format(expired)
        self.message_user(request, message, messages.SUCCESS)
    mark_as_expired.short_description = "Mark selected subscriptions as expired"

    def save_model(self, request, obj, form, change):
        """Handle subscription creation/update"""
        if not change:  # Only for new subscriptions
            # Deactivate existing active subscriptions
            UserSubscription.objects.filter(
                user=obj.user,
                status='ACTIVE'
            ).update(status='CANCELLED')
        super().save_model(request, obj, form, change)
