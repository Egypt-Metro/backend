# apps/users/admin/user_admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from ..models import User
from .filters import SubscriptionTypeFilter, UserActivityFilter
from .actions import make_premium, deactivate_users
from ..constants.choices import SubscriptionType


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    # Display configuration
    list_display = (
        'username',
        'email',
        'full_name',
        'subscription_badge',
        'balance_display',
        'last_login_display',
        'status_badge',
        'account_actions',
    )

    # Filtering and searching
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

    # Ordering and pagination
    ordering = ('-date_joined',)
    list_per_page = 25
    show_full_result_count = True

    # Actions
    actions = [make_premium, deactivate_users]
    actions_on_top = True
    actions_on_bottom = True

    # Fieldsets for add/edit forms
    fieldsets = (
        ('Account Information', {
            'fields': (
                'username',
                'email',
                'password',
                ('first_name', 'last_name'),
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
            'description': 'Manage user subscription and payment details',
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
            'description': 'User permission settings',
        }),
        ('Important Dates', {
            'fields': (
                'last_login',
                'date_joined',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',),
        }),
    )

    # Read-only fields
    readonly_fields = (
        'last_login',
        'date_joined',
        'created_at',
        'updated_at',
    )

    # Custom display methods
    def full_name(self, obj):
        """Display user's full name"""
        return f"{obj.first_name} {obj.last_name}" if obj.first_name or obj.last_name else "-"
    full_name.short_description = 'Full Name'

    def subscription_badge(self, obj):
        """Display subscription type with color-coded badge"""
        colors = {
            SubscriptionType.FREE: '#6c757d',
            SubscriptionType.BASIC: '#007bff',
            SubscriptionType.PREMIUM: '#28a745',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 0.875em;">{}</span>',
            colors.get(obj.subscription_type, '#6c757d'),
            obj.get_subscription_type_display()
        )
    subscription_badge.short_description = 'Subscription'

    def balance_display(self, obj):
        """Display formatted balance"""
        return format_html(
            '<span style="font-family: monospace;">EGP {:.2f}</span>',
            obj.balance
        )
    balance_display.short_description = 'Balance'

    def last_login_display(self, obj):
        """Display formatted last login date"""
        if obj.last_login:
            return obj.last_login.strftime("%Y-%m-%d %H:%M")
        return format_html(
            '<span style="color: #dc3545;">Never</span>'
        )
    last_login_display.short_description = 'Last Login'

    def status_badge(self, obj):
        """Display user status with color-coded badge"""
        if obj.is_active:
            return format_html(
                '<span style="background-color: #28a745; color: white; '
                'padding: 3px 8px; border-radius: 3px;">Active</span>'
            )
        return format_html(
            '<span style="background-color: #dc3545; color: white; '
            'padding: 3px 8px; border-radius: 3px;">Inactive</span>'
        )
    status_badge.short_description = 'Status'

    def account_actions(self, obj):
        """Display action buttons for each user"""
        return format_html(
            '<a class="button" href="{}">Edit</a>&nbsp;'
            '<a class="button" href="{}">History</a>',
            f'/admin/users/user/{obj.pk}/change/',
            f'/admin/users/user/{obj.pk}/history/'
        )
    account_actions.short_description = 'Actions'

    # Custom views
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'statistics/',
                self.admin_site.admin_view(self.statistics_view),
                name='user-statistics',
            ),
        ]
        return custom_urls + urls

    def statistics_view(self, request):
        """Custom view for user statistics"""
        context = {
            'title': 'User Statistics',
            'app_label': self.model._meta.app_label,
            'opts': self.model._meta,
            'has_change_permission': self.has_change_permission(request),
        }
        return render(request, 'admin/users/statistics.html', context)

    # Custom save handling
    def save_model(self, request, obj, form, change):
        """Custom save method for user model"""
        if not change:  # New user
            obj.set_password(form.cleaned_data["password"])
        elif 'password' in form.changed_data:  # Password changed
            obj.set_password(form.cleaned_data["password"])
        super().save_model(request, obj, form, change)

    # Admin site customization
    class Media:
        css = {
            'all': ('admin/css/user_admin.css',)
        }
        js = ('admin/js/user_admin.js',)


# Admin site customization
admin.site.site_header = "Egypt Metro Administration"
admin.site.site_title = "Egypt Metro Admin Portal"
admin.site.index_title = "Welcome to Egypt Metro Admin Portal"
