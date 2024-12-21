from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (    # fields to display
        "id",
        "username",
        "email",
        "first_name",
        "last_name",
        "phone_number",
        'national_id',
        "is_staff",
        "balance",
    )
    search_fields = ("username", "email", "first_name", "last_name", "phone_number", 'national_id')    # fields to search
    ordering = ("date_joined",)    # Ascending order by join date

    # Fields to make editable directly in the list view
    list_editable = (
        "first_name",
        "last_name",
        'phone_number',
        'national_id',
        "is_staff",
    )

    # Group fields logically in sections
    fieldsets = (
        (None, {
            'fields': ('username', 'email', 'password')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'national_id', 'phone_number')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        }),
        ('Audit Information', {
            'fields': ('last_login', 'date_joined')
        }),
        ('Subscription Information', {
            'fields': ('subscription_type', 'payment_method', 'balance')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    # Make the password field read-only
    readonly_fields = ('id', 'last_login', 'date_joined', 'created_at', 'updated_at')

    # Prevent password from being displayed in the list view
    def password(self, obj):
        return "*****"  # Mask password
    password.short_description = "Password"

    # Make password read-only for the detail view
    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        # Make password field read-only
        readonly_fields += ('password',)
        return readonly_fields

    # def has_delete_permission(self, request, obj=None):
    #     return False  # Disable user deletion


admin.site.site_header = "Egypt Metro"  # Customizing the admin header
admin.site.site_title = "Egypt Metro Admin Portal"  # Customizing the admin title
admin.site.index_title = "Welcome to Egypt Metro Admin Portal"  # Customizing the admin index title
