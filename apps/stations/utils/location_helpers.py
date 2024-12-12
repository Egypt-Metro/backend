# apps/stations/utils/location_helpers.py

from geopy.distance import geodesic # type: ignore
from apps.stations.models import Station


def find_nearest_station(latitude, longitude):
    user_location = (latitude, longitude)
    stations = Station.objects.exclude(latitude__isnull=True, longitude__isnull=True)

    if not stations.exists():
        return None, None

    nearest_station = min(
        stations,
        key=lambda station: geodesic(user_location, (station.latitude, station.longitude)).meters,
    )
    distance = geodesic(user_location, (nearest_station.latitude, nearest_station.longitude)).meters
    return nearest_station, distance
