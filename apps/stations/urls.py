# apps/stations/urls.py

from django.urls import path
from .views import TripDetailsView, NearestStationView, StationListView

urlpatterns = [
    path("stations-list/", StationListView.as_view(), name="stations-list"),
    path(
        "trip-details/<int:start_station_id>/<int:end_station_id>/",
        TripDetailsView.as_view(),
        name="trip-details",
    ),
    path("nearest-station/", NearestStationView.as_view(), name="nearest-station"),
]
