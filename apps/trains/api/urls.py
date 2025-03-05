# apps/trains/api/urls.py

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

# Initialize the router
router = DefaultRouter()
router.register(r"trains", views.TrainViewSet, basename="train")
router.register(r"schedules", views.ScheduleViewSet, basename="schedule")

# Define URL patterns
urlpatterns = [
    # Include router URLs
    path("", include(router.urls)),
    # Train-specific endpoints
    path("<str:train_id>/crowd/", views.TrainCrowdView.as_view(), name="train-crowd"),
    path("<str:train_id>/schedule/", views.TrainScheduleView.as_view(), name="train-schedule"),
    # Additional train views (if needed)
    path("list/", views.TrainListView.as_view(), name="train-list-custom"),
    path("<str:train_id>/details/", views.TrainDetailView.as_view(), name="train-detail-custom"),
    # station schedules
    path('station/<str:station_id>/schedules/',
         views.StationTrainSchedulesView.as_view(),
         name='station-schedules'),
    # station schedules using query parameter
    path('station-schedules/',
         views.StationTrainSchedulesView.as_view(),
         name='station-schedules-query'),

    # station schedules
    path('station-schedules/between/',
         views.StationSchedulesView.as_view(),
         name='station-schedules-between'),
    path(
        'stations/upcoming-trains/',
        views.StationUpcomingTrainsView.as_view(),
        name='station-upcoming-trains'
    ),
]
