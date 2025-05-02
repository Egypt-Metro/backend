from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from ..models.transaction import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id_short', 'user_link', 'amount', 'type', 'status', 'created_at')
    list_filter = ('type', 'status', 'created_at')
    search_fields = ('user__username', 'user__email', 'description', 'related_object_id')
    readonly_fields = ('id', 'created_at', 'updated_at', 'completed_at')
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {
            'fields': ('id', 'user', 'wallet', 'amount', 'type', 'status')
        }),
        (_('Related Information'), {
            'fields': ('payment_method', 'related_object_type', 'related_object_id')
        }),
        (_('Details'), {
            'fields': ('reference_number', 'description')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at', 'completed_at'),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'wallet', 'payment_method')

    def id_short(self, obj):
        """Display shortened ID for better readability"""
        return str(obj.id)[:8] + "..."
    id_short.short_description = 'ID'

    def user_link(self, obj):
        """Create a link to the user admin"""
        if obj.user:
            url = f"/admin/users/customuser/{obj.user.id}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return "-"
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'
