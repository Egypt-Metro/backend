# apps/users/admin/filters.py
from django.contrib.admin import SimpleListFilter
from django.utils import timezone
from datetime import timedelta
from apps.users.constants.choices import SubscriptionType


class SubscriptionTypeFilter(SimpleListFilter):
    title = 'Subscription Type'
    parameter_name = 'subscription_type'

    def lookups(self, request, model_admin):
        # Use SubscriptionType choices instead of User.SUBSCRIPTION_CHOICES
        return SubscriptionType.choices

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(subscription_type=self.value())


class UserActivityFilter(SimpleListFilter):
    title = 'User Activity'
    parameter_name = 'last_login'

    def lookups(self, request, model_admin):
        return (
            ('active', 'Active (Last 30 days)'),
            ('inactive', 'Inactive (30+ days)'),
            ('never', 'Never logged in'),
        )

    def queryset(self, request, queryset):
        thirty_days_ago = timezone.now() - timedelta(days=30)
        if self.value() == 'active':
            return queryset.filter(last_login__gte=thirty_days_ago)
        if self.value() == 'inactive':
            return queryset.filter(last_login__lt=thirty_days_ago)
        if self.value() == 'never':
            return queryset.filter(last_login__isnull=True)
