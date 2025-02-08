# apps/routes/admin.py

from django.contrib import admin
from .models import PrecomputedRoute


@admin.register(PrecomputedRoute)
class RouteAdmin(admin.ModelAdmin):
    list_display = ("start_station", "end_station", "distance", "duration")  # Key details in the list view
    search_fields = ("start_station__name", "end_station__name")  # Enable searching by station names
    list_filter = ("start_station", "end_station")  # Add filters for better navigation
    readonly_fields = ("distance", "duration", "path")  # Prevent accidental edits
    ordering = ("start_station", "end_station")  # Default ordering
    fieldsets = (
        ("Route Information", {
            "fields": ("start_station", "end_station", "distance", "duration")
        }),
        ("Path Details", {
            "fields": ("path",),
            "classes": ("collapse",),  # Collapsible for cleaner UI
        }),
    )

    def get_queryset(self, request):
        """Optimize query performance by selecting related station data."""
        return super().get_queryset(request).select_related("start_station", "end_station")
