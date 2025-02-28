# apps/trains/admin.py

from django.contrib import admin
from django.db.models import Avg, Sum
from django.urls import reverse
from django.utils.html import format_html
from import_export.admin import ImportExportModelAdmin
from rangefilter.filters import DateRangeFilter

from .models import CrowdMeasurement, Schedule, Train, TrainCar


class TrainCarInline(admin.TabularInline):
    model = TrainCar
    extra = 0
    min_num = 1
    max_num = 10
    show_change_link = True
    fields = (
        "car_number",
        "capacity",
        "current_load",
        "is_operational",
        "load_percentage",
        "crowd_status",
    )
    readonly_fields = ("load_percentage", "crowd_status")

    def load_percentage(self, obj):
        return format_html("{:.1f}%", obj.load_percentage)

    def crowd_status(self, obj):
        status = obj.crowd_status
        colors = {
            "EMPTY": "green",
            "LIGHT": "lightgreen",
            "MODERATE": "orange",
            "CROWDED": "orangered",
            "PACKED": "red",
        }
        return format_html('<span style="color: {};">{}</span>', colors.get(status, "black"), status)


class ScheduleInline(admin.TabularInline):
    model = Schedule
    extra = 0
    show_change_link = True
    fields = (
        "station",
        "arrival_time",
        "expected_crowd_level",
        "is_active",
    )
    ordering = ("arrival_time",)


@admin.register(Train)
class TrainAdmin(ImportExportModelAdmin):
    list_display = (
        "train_id",
        "line_link",
        "status_badge",
        "current_station_link",
        "direction",
        "ac_status",
        "total_passengers",
        "last_updated",
    )
    list_filter = (
        "line",
        "status",
        "has_air_conditioning",
        "direction",
        ("last_updated", DateRangeFilter),
    )
    search_fields = ("train_id", "current_station__name", "line__name")
    readonly_fields = ("last_updated", "total_passengers", "average_load")
    inlines = [TrainCarInline, ScheduleInline]
    fieldsets = (
        (
            "Basic Information",
            {"fields": ("train_id", "line", "status", "has_air_conditioning", "number_of_cars")},
        ),
        (
            "Current Status",
            {"fields": ("current_station", "next_station", "direction", "speed", "last_updated")},
        ),
        ("Location", {"fields": ("latitude", "longitude"), "classes": ("collapse",)}),
        ("Statistics", {"fields": ("total_passengers", "average_load"), "classes": ("collapse",)}),
    )
    actions = ["mark_as_maintenance", "mark_as_in_service"]

    def line_link(self, obj):
        url = reverse("admin:stations_line_change", args=[obj.line.id])
        return format_html('<a href="{}">{}</a>', url, obj.line.name)

    line_link.short_description = "Line"

    def current_station_link(self, obj):
        if obj.current_station:
            url = reverse("admin:stations_station_change", args=[obj.current_station.id])
            return format_html('<a href="{}">{}</a>', url, obj.current_station.name)
        return "-"

    current_station_link.short_description = "Current Station"

    def status_badge(self, obj):
        colors = {
            "IN_SERVICE": "green",
            "DELAYED": "orange",
            "MAINTENANCE": "red",
            "OUT_OF_SERVICE": "gray",
        }
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 7px;'
            ' border-radius: 3px;">'
            "{}"
            "</span>",
            colors.get(obj.status, "black"),
            obj.status,
        )

    status_badge.short_description = "Status"

    def ac_status(self, obj):
        if obj.has_air_conditioning:
            return format_html(
                '<span style="color: white; background-color: #28a745; padding: 3px 7px; '
                'border-radius: 3px;">AC</span>'
            )
        return format_html(
            '<span style="color: white; background-color: #dc3545; padding: 3px 7px; '
            'border-radius: 3px;">Non-AC</span>'
        )
    ac_status.short_description = "AC Status"

    def car_count(self, obj):
        return obj.cars.count()

    car_count.short_description = "Cars"

    def total_passengers(self, obj):
        return obj.cars.aggregate(total=Sum("current_load"))["total"] or 0

    total_passengers.short_description = "Total Passengers"

    def average_load(self, obj):
        avg = obj.cars.aggregate(avg=Avg("current_load"))["avg"] or 0
        return f"{avg:.1f} passengers/car"

    average_load.short_description = "Average Load"

    def mark_as_maintenance(self, request, queryset):
        updated = queryset.update(status="MAINTENANCE")
        self.message_user(request, f"{updated} trains marked as under maintenance.")

    mark_as_maintenance.short_description = "Mark selected trains as under maintenance"

    def mark_as_in_service(self, request, queryset):
        updated = queryset.update(status="IN_SERVICE")
        self.message_user(request, f"{updated} trains marked as in service.")

    mark_as_in_service.short_description = "Mark selected trains as in service"


@admin.register(TrainCar)
class TrainCarAdmin(admin.ModelAdmin):
    list_display = (
        "train_link",
        "car_number",
        "capacity",
        "current_load",
        "load_percentage_display",
        "crowd_status_badge",
        "is_operational",
    )
    list_filter = ("is_operational", "train__line")
    search_fields = ("train__train_id",)
    readonly_fields = ("last_updated",)
    actions = ["mark_as_operational", "mark_as_non_operational"]

    def load_percentage_display(self, obj):
        percentage = obj.load_percentage
        width = min(int(percentage), 100)
        color = self._get_percentage_color(percentage)

        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0;">'
            '<div style="width: {}px; background-color: {}; height: 20px;"></div>'
            '<div style="text-align: center; margin-top: -20px;">{}</div>'
            "</div>",
            width,
            color,
            "{:.1f}%".format(percentage),
        )

    load_percentage_display.short_description = "Load"

    def crowd_status_badge(self, obj):
        status = obj.crowd_status
        colors = {
            "EMPTY": "#28a745",
            "LIGHT": "#98d85b",
            "MODERATE": "#ffc107",
            "CROWDED": "#fd7e14",
            "PACKED": "#dc3545",
        }
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 7px; ' 'border-radius: 3px;">{}</span>',
            colors.get(status, "black"),
            status,
        )

    crowd_status_badge.short_description = "Status"

    def _get_percentage_color(self, percentage):
        if percentage < 30:
            return "#28a745"  # green
        elif percentage < 50:
            return "#98d85b"  # light green
        elif percentage < 70:
            return "#ffc107"  # yellow
        elif percentage < 90:
            return "#fd7e14"  # orange
        return "#dc3545"  # red

    def train_link(self, obj):
        url = reverse("admin:trains_train_change", args=[obj.train.id])
        return format_html('<a href="{}">{}</a>', url, obj.train.train_id)

    train_link.short_description = "Train"

    def mark_as_operational(self, request, queryset):
        updated = queryset.update(is_operational=True)
        self.message_user(request, "{} cars marked as operational.".format(updated))

    mark_as_operational.short_description = "Mark selected cars as operational"

    def mark_as_non_operational(self, request, queryset):
        updated = queryset.update(is_operational=False)
        self.message_user(request, "{} cars marked as non-operational.".format(updated))

    mark_as_non_operational.short_description = "Mark selected cars as non-operational"


@admin.register(Schedule)
class ScheduleAdmin(ImportExportModelAdmin):
    list_display = (
        "train_link",
        "station_link",
        "arrival_time",
        "status",
        "expected_crowd_level",
        "is_active",
    )
    list_filter = (
        "status",
        "is_active",
        "expected_crowd_level",
        "train__line",
        ("created_at", DateRangeFilter)
    )
    search_fields = ("train__train_id", "station__name")
    ordering = ("arrival_time",)
    actions = ["activate_schedules", "deactivate_schedules"]
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Basic Information", {
            "fields": (
                "train",
                "station",
            )
        }),
        ("Timing", {
            "fields": (
                "arrival_time",
            )
        }),
        ("Status", {
            "fields": (
                "status",
                "is_active",
                "expected_crowd_level",
            )
        }),
        ("Metadata", {
            "fields": (
                "created_at",
                "updated_at",
            ),
            "classes": ("collapse",)
        }),
    )

    def train_link(self, obj):
        url = reverse("admin:trains_train_change", args=[obj.train.id])
        return format_html('<a href="{}">{}</a>', url, obj.train.train_id)
    train_link.short_description = "Train"

    def station_link(self, obj):
        url = reverse("admin:stations_station_change", args=[obj.station.id])
        return format_html('<a href="{}">{}</a>', url, obj.station.name)
    station_link.short_description = "Station"

    def activate_schedules(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"{updated} schedules activated.")
    activate_schedules.short_description = "Activate selected schedules"

    def deactivate_schedules(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} schedules deactivated.")
    deactivate_schedules.short_description = "Deactivate selected schedules"


@admin.register(CrowdMeasurement)
class CrowdMeasurementAdmin(admin.ModelAdmin):
    list_display = (
        "train_car_link",
        "timestamp",
        "passenger_count",
        "crowd_percentage",
        "confidence_score",
    )
    list_filter = ("measurement_method", ("timestamp", DateRangeFilter), "train_car__train__line")
    search_fields = ("train_car__train__train_id",)
    readonly_fields = ("timestamp",)

    def formatted_crowd_percentage(self, obj):
        return f"{obj.crowd_percentage:.2f}%"
    formatted_crowd_percentage.short_description = "Crowd Percentage"

    def formatted_confidence_score(self, obj):
        return f"{obj.confidence_score:.2f}"
    formatted_confidence_score.short_description = "Confidence Score"

    def train_car_link(self, obj):
        url = reverse("admin:trains_traincar_change", args=[obj.train_car.id])
        return format_html(
            '<a href="{}">{} - Car {}</a>',
            url,
            obj.train_car.train.train_id,
            obj.train_car.car_number,
        )
    train_car_link.short_description = "Train Car"
