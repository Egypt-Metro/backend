# apps/routes/admin.py

from django.contrib import admin
from apps.routes.models import Route


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = (
        'start_station',
        'end_station',
        'primary_line',
        'number_of_stations',
        'total_distance',
        'total_time',
        'is_active',
    )

    list_filter = (
        'is_active',
        'primary_line',
        'created_at',
        ('start_station', admin.RelatedOnlyFieldListFilter),
        ('end_station', admin.RelatedOnlyFieldListFilter),
    )

    search_fields = (
        'start_station__name',
        'end_station__name',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'number_of_stations',
        'path',
        'interchanges',
    )

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'start_station',
                'end_station',
                'primary_line',
                'is_active',
            )
        }),
        ('Route Details', {
            'fields': (
                'total_distance',
                'total_time',
                'number_of_stations',
                'path',
                'interchanges',
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
