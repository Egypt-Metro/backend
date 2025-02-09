# apps/routes/urls.py

from django.urls import path
from .views import RouteView, get_shortest_route

urlpatterns = [
    path('route/<int:start_station_id>/<int:end_station_id>/', RouteView.as_view(), name='precomputed-route'),
    path('shortest/', get_shortest_route, name='shortest-route'),
]
