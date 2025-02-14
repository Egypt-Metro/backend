# apps/stations/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from .models import Line, Station, LineStation
from apps.stations.management.commands.populate_metro_data import (
    Command as MetroDataCommand,
)

# Get constants from MetroDataCommand
LINE_OPERATIONS = MetroDataCommand.LINE_OPERATIONS
CONNECTING_STATIONS = MetroDataCommand.CONNECTING_STATIONS


class LineStationInline(admin.TabularInline):
    """Inline admin for LineStation management"""

    model = LineStation
    extra = 1
    fields = ["station", "order"]
    ordering = ["order"]
    autocomplete_fields = ["station"]
    show_change_link = True

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("station", "line")


@admin.register(Line)
class LineAdmin(admin.ModelAdmin):
    """Admin configuration for Line model"""

    list_display = [
        "name",
        "color_display",
        "get_total_stations",
        "get_operational_hours",
        "get_interchanges",
    ]
    list_filter = ["name"]
    search_fields = ["name"]
    inlines = [LineStationInline]

    def color_display(self, obj):
        """Display line color as a colored box"""
        return format_html(
            '<span style="background-color: {}; padding: 5px; border-radius: 3px;">{}</span>',
            obj.color_code,
            obj.color_code,
        )

    color_display.short_description = "Color"

    def get_total_stations(self, obj):
        """Display total number of stations"""
        count = obj.stations.count()
        return f"{count} station{'s' if count != 1 else ''}"

    get_total_stations.short_description = "Stations"

    def get_operational_hours(self, obj):
        """Display operational hours"""
        try:
            weekday = LINE_OPERATIONS.get(obj.name, {}).get("weekday", {})
            if weekday:
                return f"{weekday.get('first_train', 'N/A')} - {weekday.get('last_train', 'N/A')}"
            return "N/A"
        except Exception:
            return "N/A"

    get_operational_hours.short_description = "Hours (Weekday)"

    def get_interchanges(self, obj):
        """Display interchange stations"""
        interchanges = (
            Station.objects.filter(lines=obj)
            .annotate(line_count=Count("lines"))
            .filter(line_count__gt=1)
        )
        return ", ".join([station.name for station in interchanges])

    get_interchanges.short_description = "Interchanges"


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    """Admin configuration for Station model"""

    list_display = [
        "name",
        "get_lines_display",
        "is_interchange_display",
        "get_coordinates",
        "get_connections",
    ]
    list_filter = [
        "lines__name",
        "station_lines__line__name",
        ("lines", admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = ["name", "lines__name"]
    inlines = [LineStationInline]
    fieldsets = (
        (None, {"fields": ("name",)}),
        ("Location", {"fields": ("latitude", "longitude"), "classes": ("collapse",)}),
    )

    def get_lines_display(self, obj):
        """Display lines with their colors"""
        return format_html(
            " ".join(
                f'<span style="background-color: {line.color_code}; '
                f'padding: 3px 7px; border-radius: 3px; margin: 0 2px;">'
                f"{line.name}</span>"
                for line in obj.lines.all()
            )
        )

    get_lines_display.short_description = "Lines"

    def is_interchange_display(self, obj):
        """Display interchange status with icon"""
        is_interchange = obj.lines.count() > 1
        icon = "✓" if is_interchange else "✗"
        color = "green" if is_interchange else "red"
        return format_html(f'<span style="color: {color};">{icon}</span>')

    is_interchange_display.short_description = "Interchange"
    is_interchange_display.boolean = True

    def get_coordinates(self, obj):
        """Display coordinates with link to map"""
        if obj.latitude and obj.longitude:
            return format_html(
                '<a href="https://www.google.com/maps?q={},{}" target="_blank">'
                "{:.6f}, {:.6f}</a>",
                obj.latitude,
                obj.longitude,
                obj.latitude,
                obj.longitude,
            )
        return "N/A"

    get_coordinates.short_description = "Location"

    def get_connections(self, obj):
        """Display connecting stations"""
        if not obj.is_interchange():
            return "-"
        connections = []
        for conn in CONNECTING_STATIONS:
            if conn["name"] == obj.name:
                connections.extend(conn["lines"])
        return " ↔ ".join(connections) if connections else "-"

    get_connections.short_description = "Connections"


@admin.register(LineStation)
class LineStationAdmin(admin.ModelAdmin):
    """Admin configuration for LineStation model"""

    list_display = [
        "line",
        "station",
        "order",
        "get_next_station",
        "get_distance_to_next",
    ]
    list_filter = ["line__name", "station__name"]
    search_fields = ["line__name", "station__name"]
    ordering = ["line", "order"]

    def get_next_station(self, obj):
        """Display next station in sequence"""
        next_station = LineStation.objects.filter(
            line=obj.line, order=obj.order + 1
        ).first()
        return next_station.station.name if next_station else "-"

    get_next_station.short_description = "Next Station"

    def get_distance_to_next(self, obj):
        """Display distance to next station"""
        next_station = LineStation.objects.filter(
            line=obj.line, order=obj.order + 1
        ).first()
        if next_station:
            distance = obj.station.distance_to(next_station.station)
            return f"{distance / 1000:.2f} km"
        return "-"

    get_distance_to_next.short_description = "Distance to Next"
