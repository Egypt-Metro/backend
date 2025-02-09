# apps/routes/admin.py

from django.contrib import admin
from apps.routes.models import PrecomputedRoute


@admin.register(PrecomputedRoute)
class PrecomputedRouteAdmin(admin.ModelAdmin):
    """
    Admin interface for managing PrecomputedRoute objects.
    Precomputed routes are managed programmatically, so add/delete permissions are restricted.
    """

    # List display configuration
    list_display = (
        "start_station",
        "end_station",
        "line",
        "get_path_length",
        "get_interchange_count",
    )
    list_filter = ("line",)
    search_fields = (
        "start_station__name",
        "end_station__name",
        "line__name",
    )
    ordering = ("start_station", "end_station", "line")

    # Fieldsets for the edit form
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "start_station",
                    "end_station",
                    "line",
                )
            },
        ),
        (
            "Route Details",
            {
                "fields": (
                    "path",
                    "interchanges",
                ),
                "classes": ("collapse",),  # Collapsible section
            },
        ),
    )

    # Read-only fields to prevent accidental modifications
    readonly_fields = (
        "path",
        "interchanges",
    )

    # Custom methods for list display
    def get_path_length(self, obj):
        """Returns the number of stations in the path."""
        return len(obj.path) if obj.path else 0

    get_path_length.short_description = "Path Length"

    def get_interchange_count(self, obj):
        """Returns the number of interchanges in the route."""
        return len(obj.interchanges) if obj.interchanges else 0

    get_interchange_count.short_description = "Interchanges"

    # Permissions
    def has_add_permission(self, request):
        """Precomputed routes should be managed programmatically."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Restrict deletion to avoid breaking route caching."""
        return False
