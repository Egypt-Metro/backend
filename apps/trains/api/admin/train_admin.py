# apps/trains/admin/train_admin.py

from django.contrib import admin
from apps.trains.models.train import Train, TrainCar
from apps.trains.models.schedule import Schedule


@admin.register(Train)
class TrainAdmin(admin.ModelAdmin):
    list_display = ['train_number', 'line', 'status', 'direction', 'current_station']
    list_filter = ['line', 'status', 'has_ac']
    search_fields = ['train_number']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TrainCar)
class TrainCarAdmin(admin.ModelAdmin):
    list_display = ['train', 'car_number', 'has_camera', 'current_passengers', 'crowd_level']
    list_filter = ['has_camera', 'crowd_level']
    search_fields = ['train__train_number']


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['train', 'station', 'arrival_time', 'departure_time', 'status']
    list_filter = ['status', 'station']
    search_fields = ['train__train_number', 'station__name']
