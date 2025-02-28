# apps/users/admin/actions.py
from django.contrib import messages
from django.utils.translation import ngettext
from apps.users.constants.choices import SubscriptionType


def make_premium(modeladmin, request, queryset):
    updated = queryset.update(subscription_type=SubscriptionType.PREMIUM)
    modeladmin.message_user(
        request,
        ngettext(
            '%d user was successfully marked as Premium.',
            '%d users were successfully marked as Premium.',
            updated,
        ) % updated,
        messages.SUCCESS
    )


def deactivate_users(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    modeladmin.message_user(
        request,
        ngettext(
            '%d user was successfully deactivated.',
            '%d users were successfully deactivated.',
            updated,
        ) % updated,
        messages.WARNING
    )
