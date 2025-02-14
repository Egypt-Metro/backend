# apps/routes/views.py

from rest_framework import views, status
from rest_framework.response import Response
from .services.route_service import MetroRouteService
from .models import Route
from apps.stations.models import Station
from django.core.exceptions import ValidationError


class RouteView(views.APIView):
    """
    API endpoint for finding routes between metro stations.

    GET Parameters:
        start (str): Name of the starting station
        end (str): Name of the destination station

    Returns:
        route (list): List of stations in the route
        total_distance (float): Total distance in kilometers
        num_stations (int): Number of stations in the route
        interchanges (list): List of interchange points
    """
    route_service = MetroRouteService()

    def get(self, request):
        try:
            # Validate input
            start_station_name = request.query_params.get('start')
            end_station_name = request.query_params.get('end')

            if not start_station_name or not end_station_name:
                return Response(
                    {"error": "Both start and end stations are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if start_station_name == end_station_name:
                return Response(
                    {"error": "Start and end stations cannot be the same"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                start_station = Station.objects.get(name__iexact=start_station_name)
                end_station = Station.objects.get(name__iexact=end_station_name)
            except Station.DoesNotExist:
                return Response(
                    {"error": "One or both stations not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Check for existing route
            existing_route = Route.objects.filter(
                start_station=start_station,
                end_station=end_station,
                is_active=True
            ).first()

            if existing_route:
                return Response({
                    "route": existing_route.path,
                    "total_distance": round(existing_route.total_distance, 2),
                    "num_stations": existing_route.number_of_stations,
                    "interchanges": existing_route.interchanges
                })

            # Find new route
            route = self.route_service.find_route(start_station.id, end_station.id)

            if not route:
                return Response(
                    {"error": "No route found between these stations"},
                    status=status.HTTP_404_NOT_FOUND
                )

            return Response({
                "route": route['path'],
                "total_distance": round(route['distance'], 2),
                "num_stations": route['num_stations'],
                "interchanges": route['interchanges']
            })

        except ValidationError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
