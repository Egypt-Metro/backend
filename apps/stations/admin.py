# apps/stations/admin.py

from django.contrib import admin
from .models import Line, Station, LineStation

class LineStationInline(admin.TabularInline):
    """
    Inline admin for LineStation to manage the relationship between lines and stations.
    """
    model = LineStation
    extra = 1
    fields = ["station", "order"]
    ordering = ["order"]


@admin.register(Line)
class LineAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Line model.
    """
    list_display = ("name", "color_code", "total_stations")
    search_fields = ("name",)
    inlines = [LineStationInline]


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Station model.
    """
    list_display = ("name", "latitude", "longitude", "is_interchange")
    search_fields = ("name",)
    inlines = [LineStationInline]  # Use the inline for managing lines
    fieldsets = (
        (None, {
            "fields": ("name", "latitude", "longitude"),
        }),
    )


@admin.register(LineStation)
class LineStationAdmin(admin.ModelAdmin):
    """
    Admin configuration for the LineStation model.
    """
    list_display = ("line", "station", "order")
    list_filter = ("line",)
    ordering = ["line", "order"]
