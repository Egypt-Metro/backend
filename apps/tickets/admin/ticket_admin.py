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
        'user',
        'status_colored',
        'price',
        'entry_station',
        'exit_station',
        'valid_until',
        'is_active',
        'created_at'
    ]
    list_filter = [
        'status',
        'price_category',
        'entry_station',
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
                'price_category',
                'price',
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

    def is_active(self, obj):
        """Check if ticket is still active"""
        return obj.valid_until > timezone.now()
    is_active.boolean = True
    is_active.short_description = 'Active'

    def status_colored(self, obj):
        """Display status with color coding"""
        colors = {
            'ACTIVE': 'green',
            'IN_USE': 'blue',
            'USED': 'grey',
            'EXPIRED': 'red',
            'CANCELLED': 'red',
            'PENDING': 'orange'
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.status, 'black'),
            obj.get_status_display()
        )
    status_colored.short_description = 'Status'

    def qr_code_display(self, obj):
        """Display QR code in admin"""
        if obj.qr_code:
            return format_html(
                '<div style="text-align: center;">'
                '<img src="data:image/png;base64,{}" width="150" height="150" style="border: 1px solid #ddd; padding: 5px;"/>'
                '</div>',
                obj.qr_code
            )
        return format_html(
            '<div style="color: #999; text-align: center;">No QR Code</div>'
        )
    qr_code_display.short_description = 'QR Code'
