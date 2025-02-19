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
]

# API Endpoint Documentation
"""
Available Endpoints:

Default Router Endpoints:
- GET    /trains/                - List all trains
- POST   /trains/                - Create a new train
- GET    /trains/{id}/          - Retrieve a train
- PUT    /trains/{id}/          - Update a train
- PATCH  /trains/{id}/          - Partially update a train
- DELETE /trains/{id}/          - Delete a train
- GET    /schedules/            - List all schedules
- POST   /schedules/            - Create a new schedule
- GET    /schedules/{id}/       - Retrieve a schedule
- PUT    /schedules/{id}/       - Update a schedule
- PATCH  /schedules/{id}/       - Partially update a schedule
- DELETE /schedules/{id}/       - Delete a schedule

Custom Endpoints:
- GET    /trains/{train_id}/crowd/    - Get crowd information for a train
- GET    /trains/{train_id}/schedule/ - Get schedule for a train
- GET    /trains/list/                - Custom train listing endpoint
- GET    /trains/{train_id}/details/  - Custom train details endpoint

Router Additional Actions:
- GET    /trains/train_status/        - Get train status
- GET    /trains/line_trains/         - Get trains by line
- GET    /schedules/station_schedule/ - Get schedule by station
"""
