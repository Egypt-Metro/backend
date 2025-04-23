# admin/ticket_admin.py
from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from rangefilter.filters import DateRangeFilter
from ..models.ticket import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = [
        'ticket_number',
        'get_username',
        'ticket_type_colored',
        'status_colored',
        'entry_station',
        'exit_station',
        'is_active',
    ]
    list_filter = [
        'ticket_type',
        'status',
        'entry_station',
        'color',
        ('valid_until', DateRangeFilter),
        ('created_at', DateRangeFilter)
    ]
    search_fields = [
        'ticket_number',
        'user__username',
        'user__email',
        'entry_station__name',
        'exit_station__name'
    ]
    readonly_fields = [
        'ticket_number',
        'uuid',
        'qr_code_display',
        'created_at',
        'updated_at'
    ]
    raw_id_fields = ['user', 'entry_station', 'exit_station']
    date_hierarchy = 'created_at'
    list_per_page = 20

    fieldsets = (
        ('Identification', {
            'fields': (
                'ticket_number',
                'uuid',
                'user'
            )
        }),
        ('Ticket Details', {
            'fields': (
                'ticket_type',
                'price',
                'color',
                'max_stations',
                'status'
            )
        }),
        ('Station Information', {
            'fields': (
                'entry_station',
                'exit_station',
                'entry_time',
                'exit_time'
            )
        }),
        ('Validity & QR', {
            'fields': (
                'valid_until',
                'qr_code_display',
                'validation_hash'
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

    def get_username(self, obj):
        """Get username of ticket owner"""
        return obj.user.username if obj.user else '-'
    get_username.short_description = 'Username'
    get_username.admin_order_field = 'user__username'

    def is_active(self, obj):
        """Check if ticket is still active"""
        if not obj.valid_until:
            return False
        return obj.valid_until > timezone.now()
    is_active.boolean = True
    is_active.short_description = 'Active'

    def status_colored(self, obj):
        """Display status with color coding"""
        colors = {
            'ACTIVE': 'green',
            'IN_USE': 'blue',
            'USED': 'grey',
            'USED_UPGRADED': 'purple',
            'EXPIRED': 'red',
            'CANCELLED': 'red',
            'PENDING': 'orange',
            'REFUNDED': 'brown'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_colored.short_description = 'Status'

    def ticket_type_colored(self, obj):
        """Display ticket type with its designated color"""
        ticket_colors = {
            'BASIC': 'gold',
            'STANDARD': 'green',
            'PREMIUM': 'red',
            'VIP': 'blue'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            ticket_colors.get(obj.ticket_type, 'black'),
            obj.ticket_type
        )
    ticket_type_colored.short_description = 'Ticket Type'

    def qr_code_display(self, obj):
        """Display QR code in admin"""
        if obj.qr_code:
            return format_html(
                '<div style="text-align: center;">'
                '<img src="data:image/png;base64,{}" width="150" height="150" '
                'style="border: 1px solid #ddd; padding: 5px; border-radius: 4px;"/>'
                '</div>',
                obj.qr_code
            )
        return format_html(
            '<div style="color: #999; text-align: center; padding: 10px;">'
            'No QR Code Available</div>'
        )
    qr_code_display.short_description = 'QR Code'

    def get_queryset(self, request):
        """Optimize queryset for admin list view"""
        return super().get_queryset(request).select_related(
            'user',
            'entry_station',
            'exit_station'
        )

    def save_model(self, request, obj, form, change):
        """Record the user who made the change"""
        if not change:  # If this is a new ticket
            if not obj.user:
                obj.user = request.user
        super().save_model(request, obj, form, change)
