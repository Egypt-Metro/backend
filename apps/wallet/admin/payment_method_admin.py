from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from ..models.payment_method import PaymentMethod


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'payment_type', 'card_last4', 'is_default', 'is_active')
    list_filter = ('payment_type', 'is_default', 'is_active', 'created_at')
    search_fields = ('name', 'user__username', 'user__email', 'card_last4')
    readonly_fields = ('id', 'created_at', 'updated_at')

    fieldsets = (
        (None, {
            'fields': ('id', 'user', 'name', 'payment_type')
        }),
        (_('Card Details'), {
            'fields': ('card_last4', 'card_brand', 'card_expiry_month', 'card_expiry_year')
        }),
        (_('Status'), {
            'fields': ('is_default', 'is_active')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
