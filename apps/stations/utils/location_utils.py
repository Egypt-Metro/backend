# apps/stations/utils/location_utils.py

from typing import List, Tuple, Optional
from venv import logger
from django.db.models import F, ExpressionWrapper, FloatField
from django.db.models.functions import ACos, Cos, Radians, Sin
from apps.stations.models import Station
import math


def find_nearest_station(latitude: float, longitude: float) -> Tuple[Optional[Station], float]:
    """Find nearest station to given coordinates."""
    try:
        stations = Station.objects.annotate(
            distance=ExpressionWrapper(
                6371 * ACos(
                    Cos(Radians(latitude))
                    * Cos(Radians(F('latitude')))
                    * Cos(Radians(F('longitude')) - Radians(longitude))
                    + Sin(Radians(latitude))
                    * Sin(Radians(F('latitude')))
                ),
                output_field=FloatField()
            )
        ).order_by('distance')

        nearest = stations.first()
        if nearest:
            return nearest, nearest.distance * 1000  # Convert to meters
        return None, float('inf')
    except Exception as e:
        logger.error(f"Error finding nearest station: {str(e)}")
        return None, float('inf')


class LocationUtils:
    @staticmethod
    def find_stations_within_radius(
        latitude: float, longitude: float, radius_km: float
    ) -> List[Station]:
        """
        Finds all stations within a given radius using database-level calculations.
        """
        try:
            stations = (
                Station.objects.annotate(
                    distance=ExpressionWrapper(
                        6371
                        * ACos(
                            Cos(Radians(latitude))
                            * Cos(Radians(F("latitude")))
                            * Cos(Radians(F("longitude")) - Radians(longitude))
                            + Sin(Radians(latitude)) * Sin(Radians(F("latitude")))
                        ),
                        output_field=FloatField(),
                    )
                )
                .filter(distance__lte=radius_km)
                .order_by("distance")
            )

            return list(stations)
        except Exception as e:
            logger.error(f"Error finding stations within radius: {str(e)}")
            return []

    @staticmethod
    def calculate_route_distance(stations: List[Station]) -> float:
        """
        Calculates total distance of a route through given stations.
        """
        try:
            total_distance = 0
            for i in range(len(stations) - 1):
                total_distance += stations[i].distance_to(stations[i + 1])
            return total_distance
        except Exception as e:
            logger.error(f"Error calculating route distance: {str(e)}")
            return 0.0

    @staticmethod
    def calculate_distance_between_coordinates(
        lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """
        Calculate distance between two points using Haversine formula.
        Returns distance in meters.
        """
        try:
            R = 6371000  # Earth's radius in meters

            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1

            a = (
                math.sin(dlat / 2) ** 2
                + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
            )
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            distance = R * c

            return distance
        except Exception as e:
            logger.error(f"Error calculating distance between coordinates: {str(e)}")
            return 0.0

    @staticmethod
    def get_bounding_box(latitude: float, longitude: float, radius_km: float) -> dict:
        """
        Calculate a bounding box around a point for quick spatial queries.
        """
        try:
            # Approximate degrees to add/subtract
            lat_change = radius_km / 111.0
            lon_change = radius_km / (111.0 * math.cos(math.radians(latitude)))

            return {
                "min_lat": latitude - lat_change,
                "max_lat": latitude + lat_change,
                "min_lon": longitude - lon_change,
                "max_lon": longitude + lon_change,
            }
        except Exception as e:
            logger.error(f"Error calculating bounding box: {str(e)}")
            return {
                "min_lat": latitude,
                "max_lat": latitude,
                "min_lon": longitude,
                "max_lon": longitude,
            }
