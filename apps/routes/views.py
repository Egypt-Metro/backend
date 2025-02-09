import logging
import traceback
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from apps.stations.models import Station
from apps.routes.models import PrecomputedRoute
from apps.routes.services.cache_service import CacheService
from apps.routes.services.route_service import RouteService

logger = logging.getLogger(__name__)


class RouteView(APIView):
    """
    API endpoint to retrieve a precomputed route between two stations.
    Checks the cache first, then queries the database if needed.
    """

    def get(self, request, start_station_id, end_station_id):
        try:
            start_station, end_station = self._validate_stations(start_station_id, end_station_id)

            # Check cache first
            cache_key = CacheService._generate_cache_key(start_station_id, end_station_id)
            cached_route = CacheService.get_cached_route(cache_key)
            if cached_route:
                logger.info(f"Returning cached route for {start_station_id} -> {end_station_id}")
                return Response(cached_route)

            # Fetch from database
            route = PrecomputedRoute.objects.filter(
                start_station=start_station,
                end_station=end_station
            ).only("path", "interchanges").first()

            if not route:
                logger.warning(f"No precomputed route found for {start_station_id} -> {end_station_id}")
                return Response({"error": "Route not found."}, status=status.HTTP_404_NOT_FOUND)

            # Cache and return route data
            route_data = {
                "path": route.path,
                "interchanges": route.interchanges
            }
            CacheService.cache_route(cache_key, route_data)
            logger.info(f"Route cached for {start_station_id} -> {end_station_id}")
            return Response(route_data)

        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _validate_stations(self, start_station_id, end_station_id):
        """ Validates and fetches station objects. """
        try:
            return (
                get_object_or_404(Station, id=int(start_station_id)),
                get_object_or_404(Station, id=int(end_station_id))
            )
        except (ValueError, TypeError):
            logger.error("Invalid station ID format. IDs must be integers.")
            raise ValidationError("Station IDs must be valid integers.")


@api_view(["GET"])
def get_shortest_route(request):
    """
    API endpoint to compute and return the shortest route between two stations.
    Checks cache first, otherwise computes and caches the result.
    """
    start_station_id = request.GET.get("start_station")
    end_station_id = request.GET.get("end_station")

    if not start_station_id or not end_station_id:
        logger.error("Missing start_station or end_station in query parameters.")
        return Response({"error": "Both start_station and end_station are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        start_station, end_station = _validate_stations(start_station_id, end_station_id)
        cached_route = CacheService.get_cached_route(start_station_id, end_station_id)

        if cached_route:
            logger.info(f"Returning cached route for {start_station_id} -> {end_station_id}")
            return Response(cached_route)

        route_data = RouteService.find_shortest_path(start_station, end_station)
        if not route_data:
            logger.warning(f"No computed route found for {start_station_id} -> {end_station_id}")
            return Response({"error": "No route found between the specified stations."}, status=status.HTTP_404_NOT_FOUND)

        CacheService.cache_route(start_station_id, end_station_id, route_data)
        logger.info(f"Computed and cached route for {start_station_id} -> {end_station_id}")
        return Response(route_data)

    except ValidationError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
        return Response({"error": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _validate_stations(start_station_id, end_station_id):
    """ Helper function to validate and fetch station objects. """
    try:
        return (
            get_object_or_404(Station, id=int(start_station_id)),
            get_object_or_404(Station, id=int(end_station_id))
        )
    except (ValueError, TypeError):
        logger.error("Invalid station ID format. IDs must be integers.")
        raise ValidationError("Station IDs must be valid integers.")
