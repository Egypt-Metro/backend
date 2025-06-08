from django.contrib import admin
from .models import (
    StationAnalytics,
    LineAnalytics,
    TicketUsageRecord,
    SubscriptionUsageRecord,
    DailyAnalytics
)


@admin.register(StationAnalytics)
class StationAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('station', 'total_revenue', 'tickets_scanned', 'subscriptions_used', 'last_updated')
    search_fields = ('station__name',)
    list_filter = ('station__lines',)
    readonly_fields = ('total_revenue', 'ticket_revenue', 'subscription_revenue',
                       'tickets_scanned', 'subscriptions_used', 'total_entries', 'last_updated')


@admin.register(LineAnalytics)
class LineAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('line', 'total_revenue', 'tickets_scanned', 'subscriptions_used', 'last_updated')
    search_fields = ('line__name',)
    readonly_fields = ('total_revenue', 'ticket_revenue', 'subscription_revenue',
                       'tickets_scanned', 'subscriptions_used', 'total_entries', 'last_updated')


@admin.register(TicketUsageRecord)
class TicketUsageRecordAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'station', 'line', 'revenue_amount', 'timestamp')
    list_filter = ('station', 'line', 'timestamp')
    search_fields = ('ticket__id', 'station__name', 'line__name')
    date_hierarchy = 'timestamp'


@admin.register(SubscriptionUsageRecord)
class SubscriptionUsageRecordAdmin(admin.ModelAdmin):
    list_display = ('subscription', 'station', 'line', 'revenue_amount', 'timestamp')
    list_filter = ('station', 'line', 'timestamp')
    search_fields = ('subscription__id', 'station__name', 'line__name')
    date_hierarchy = 'timestamp'


@admin.register(DailyAnalytics)
class DailyAnalyticsAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_revenue', 'ticket_revenue', 'subscription_revenue', 'total_entries')
    date_hierarchy = 'date'
    readonly_fields = ('total_revenue', 'ticket_revenue', 'subscription_revenue',
                       'tickets_scanned', 'subscriptions_used', 'total_entries')
