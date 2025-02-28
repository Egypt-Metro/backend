from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import admin
from django.utils.html import format_html
from .filters import SubscriptionTypeFilter, UserActivityFilter
from .actions import make_premium, deactivate_users
from ..constants.choices import SubscriptionType


class UserAdmin(BaseUserAdmin):
    """Enhanced UserAdmin with custom functionality"""

    list_display = (
        'username',
        'email',
        'get_full_name',
        'subscription_badge',
        'balance_display',
        'is_active',
    )

    list_filter = (
        SubscriptionTypeFilter,
        UserActivityFilter,
        'is_active',
        'is_staff',
        'payment_method',
        ('date_joined', admin.DateFieldListFilter),
    )

    search_fields = (
        'username',
        'email',
        'first_name',
        'last_name',
        'phone_number',
        'national_id',
    )

    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal Information', {
            'fields': (
                ('first_name', 'last_name'),
                'email',
                'phone_number',
                'national_id',
            )
        }),
        ('Subscription & Payment', {
            'fields': (
                'subscription_type',
                'payment_method',
                'balance',
            ),
            'classes': ('collapse',),
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            ),
            'classes': ('collapse',),
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'password1',
                'password2',
                'first_name',
                'last_name',
                'subscription_type',
            ),
        }),
    )

    readonly_fields = ('last_login', 'date_joined')
    ordering = ('-date_joined',)
    list_per_page = 25
    actions = [make_premium, deactivate_users]
    filter_horizontal = ('groups', 'user_permissions',)

    def get_full_name(self, obj):
        """Get user's full name with proper fallback"""
        if obj.first_name and obj.last_name:
            return f"{obj.first_name} {obj.last_name}"
        elif obj.first_name:
            return obj.first_name
        elif obj.last_name:
            return obj.last_name
        return obj.username
    get_full_name.short_description = 'Full Name'

    def subscription_badge(self, obj):
        """Display subscription type with color-coded badge"""
        colors = {
            SubscriptionType.FREE: '#6c757d',
            SubscriptionType.BASIC: '#007bff',
            SubscriptionType.PREMIUM: '#28a745',
        }
        color = colors.get(obj.subscription_type, '#6c757d')
        text = obj.get_subscription_type_display()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px;">{}</span>',
            color, text
        )
    subscription_badge.short_description = 'Subscription'

    def balance_display(self, obj):
        """Display formatted balance with currency"""
        balance = obj.balance if obj.balance is not None else 0.00
        return format_html(
            '{:.2f}'.format(balance)
        )
    balance_display.short_description = 'Balance'

    def save_model(self, request, obj, form, change):
        """Handle user creation and password updates"""
        if not change:  # New user
            obj.set_password(form.cleaned_data["password1"])
        elif 'password' in form.changed_data:  # Password changed
            obj.set_password(form.cleaned_data["password"])
        super().save_model(request, obj, form, change)
