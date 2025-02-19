# apps/stations/admin.py

from venv import logger

import markupsafe
from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from apps.stations.management.commands.populate_metro_data import Command as MetroDataCommand
from metro import settings

from .models import Line, LineStation, Station

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
        interchanges = Station.objects.filter(lines=obj).annotate(line_count=Count("lines")).filter(line_count__gt=1)
        return ", ".join([station.name for station in interchanges])

    get_interchanges.short_description = "Interchanges"


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    """Admin configuration for Station model"""

    list_display = [
        "name",
        "get_lines_display",
        "is_interchange_display",  # Use the modified method
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

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super().get_search_results(request, queryset, search_term)

        if "autocomplete" in request.path:
            queryset = queryset.prefetch_related("lines")

        return queryset, use_distinct

    def format_json(self, obj):
        return {"id": obj.id, "text": obj.name, "lines": ", ".join(line.name for line in obj.lines.all())}

    def formatted_name(self, obj):
        """Display station name with its lines"""
        lines = ", ".join(line.name for line in obj.lines.all())
        return f"{obj.name} ({lines})"

    def is_interchange_display(self, obj):
        """Display interchange status"""
        return obj.lines.count() > 1

    is_interchange_display.boolean = True
    is_interchange_display.short_description = "Interchange"

    def get_lines_display(self, obj):
        """Display lines without colors"""
        return ", ".join([line.name for line in obj.lines.all()])

    get_lines_display.short_description = "Lines"

    def is_interchange_status(self, obj):
        """
        Custom method to display interchange status with a more robust approach
        """
        try:
            # Determine interchange status
            is_interchange = obj.lines.count() > 1

            # Use Django's built-in boolean icon method
            return markupsafe(
                '<img src="{}" alt="{}" style="width:16px; height:16px;">'.format(
                    f'/static/admin/img/icon-{"yes" if is_interchange else "no"}.svg', "Yes" if is_interchange else "No"
                )
            )
        except Exception as e:
            if settings.DEBUG:
                print(f"Error in is_interchange_status: {e}")
            return markupsafe('<span style="color:red;">Error</span>')

    is_interchange_status.short_description = "Interchange"
    is_interchange_status.boolean = True

    def get_coordinates(self, obj):
        """Display coordinates with link to map"""
        try:
            # Check if coordinates exist and are valid
            if (
                obj.latitude is not None
                and obj.longitude is not None
                and isinstance(obj.latitude, (int, float))
                and isinstance(obj.longitude, (int, float))
            ):
                # Safely convert to float and round
                lat = round(float(obj.latitude), 6)
                lon = round(float(obj.longitude), 6)

                # Validate coordinate ranges
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return format_html(
                        '<a href="https://www.google.com/maps?q={},{}" target="_blank">{}, {}</a>', lat, lon, lat, lon
                    )

            logger.warning(f"Invalid coordinates for station {obj.name}: Lat {obj.latitude}, Lon {obj.longitude}")
            return "N/A"
        except Exception as e:
            # Log the full error
            logger.error(f"Coordinate error for station {obj.name}: {e}", exc_info=True)
            return "Invalid Coordinates"

    get_coordinates.short_description = "Location"

    def get_connections(self, obj):
        """Display connecting stations"""
        try:
            if not obj.is_interchange():
                return "-"

            connections = []
            for conn in CONNECTING_STATIONS:
                if conn["name"] == obj.name:
                    connections.extend(conn["lines"])

            return " ↔ ".join(connections) if connections else "-"
        except Exception as e:
            if settings.DEBUG:
                print(f"Error in get_connections: {e}")
            return "Error"

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
        try:
            next_station = LineStation.objects.filter(line=obj.line, order=obj.order + 1).first()
            return next_station.station.name if next_station else "-"
        except Exception as e:
            if settings.DEBUG:
                print(f"Error in get_next_station: {e}")
            return "Error"

    def get_distance_to_next(self, obj):
        """Display distance to next station"""
        try:
            next_station = LineStation.objects.filter(line=obj.line, order=obj.order + 1).first()
            if next_station:
                distance = obj.station.distance_to(next_station.station)
                return f"{distance / 1000:.2f} km"
            return "-"
        except Exception as e:
            if settings.DEBUG:
                print(f"Error in get_distance_to_next: {e}")
            return "Error"

    get_distance_to_next.short_description = "Distance to Next"
