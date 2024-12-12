# apps/stations/admin.py

from django.contrib import admin
from .models import Line, Station, LineStation

class LineStationInline(admin.TabularInline):
    """
    Inline admin for LineStation to manage the relationship between lines and stations.
    """
    model = LineStation     # model to display     
    extra = 1   # number of extra fields to display   
    fields = ["station", "order"]   # fields to display   
    ordering = ["order"]    # order by order


@admin.register(Line)
class LineAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Line model.
    """
    list_display = ("name", "total_stations")  # fields to display
    search_fields = ("name",)   # fields to search
    inlines = [LineStationInline]   # inline to display


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Station model.
    """
    list_display = ("name", "is_interchange")  # fields to display
    search_fields = ("name",)   # fields to search
    inlines = [LineStationInline]   # inline to display  
    fieldsets = (
        (None, {
            "fields": ("name", "latitude", "longitude"),    # fields to display
        }),
    )


@admin.register(LineStation)
class LineStationAdmin(admin.ModelAdmin):
    """
    Admin configuration for the LineStation model.
    """
    list_display = ("line", "station", "order")  # fields to display
    list_filter = ("line",)    # fields to filter
    ordering = ["line", "order"]    # order by line and order
