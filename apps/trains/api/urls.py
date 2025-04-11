# apps/trains/api/urls.py

from django.urls import path
from .views.train_views import TrainViewSet

app_name = 'trains'

# URL patterns for Train API endpoints
urlpatterns = [
    # Public Endpoints
    path(
        'debug/',
        TrainViewSet.as_view({'get': 'debug_info'}),
        name='debug-info'
    ),
    path(
        'get-schedules/',
        TrainViewSet.as_view({'post': 'get_schedules'}),
        name='get-schedules'
    ),
    path(
        '',
        TrainViewSet.as_view({
            'get': 'list',
            'post': 'create'
        }),
        name='train-list'
    ),
    path(
        '<int:pk>/',
        TrainViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy'
        }),
        name='train-detail'
    ),
    path(
        '<int:pk>/station-schedule/',
        TrainViewSet.as_view({'get': 'station_schedule'}),
        name='station-schedule'
    ),

    # Protected Endpoints
    path(
        '<int:pk>/update-crowd-level/',
        TrainViewSet.as_view({'post': 'update_crowd_level'}),
        name='update-crowd'
    ),
    path(
        '<int:pk>/update-location/',
        TrainViewSet.as_view({'post': 'update_location'}),
        name='update-location'
    ),
    path(
        '<int:pk>/crowd-status/',
        TrainViewSet.as_view({'get': 'get_crowd_status'}),
        name='crowd-status'
    ),
]
