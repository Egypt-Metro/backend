# apps/stations/views.py

from rest_framework import generics, status  # Import generics for ListAPIView
from rest_framework.permissions import AllowAny  # Import AllowAny for public access
from rest_framework.views import APIView  # Import APIView for creating API views
from rest_framework.response import (
    Response,
)  # Import Response for sending JSON responses
from django.db.models import Q  # Import Q for complex queries
from apps.stations.models import Station  # Import the Station model
from .serializers import StationSerializer  # Import the StationSerializer
from .pagination import StandardResultsSetPagination  # Import the pagination class
from apps.stations.services.ticket_service import (
    calculate_ticket_price,
)  # Import the ticket price calculation service
from apps.stations.utils.location_helpers import (
    find_nearest_station,
)  # Import the find_nearest_station function


# Create your views here.
class StationListView(generics.ListAPIView):
    queryset = Station.objects.all()  # Get all stations
    serializer_class = StationSerializer  # Use the StationSerializer
    pagination_class = StandardResultsSetPagination  # Apply pagination
    permission_classes = [AllowAny]  # Allow access

    def get_queryset(self):
        """
        Retrieves a paginated list of stations, with optional search filtering (name or line name).
        """
        queryset = Station.objects.all()
        search_term = self.request.query_params.get("search", None)

        if search_term:
            queryset = queryset.filter(  # Filter stations by name or line name
                Q(name__icontains=search_term)
                | Q(  # Case-insensitive search by station name
                    lines__name__icontains=search_term
                )  # Case-insensitive search by line name
            ).distinct()  # Remove duplicates

        queryset = queryset.prefetch_related(
            "lines"
        )  # Optimize querying of related lines
        return queryset  # Return the filtered queryset


class TripDetailsView(APIView):
    """
    Provides trip details between two stations, including ticket price, travel time, and distance.
    """

    permission_classes = [AllowAny]  # Public access

    def get(self, request, start_station_id, end_station_id):
        try:
            # Get stations
            start_station = Station.objects.get(id=start_station_id)
            end_station = Station.objects.get(id=end_station_id)

            # Calculate ticket price using the service
            ticket_price = calculate_ticket_price(start_station, end_station)

            # Number of stations between start and end
            num_stations = (
                abs(
                    start_station.get_station_order(start_station.lines.first())
                    - end_station.get_station_order(end_station.lines.first())
                )
                + 1
            )

            # Estimated travel time (in minutes)
            travel_time = num_stations * 2  # 2 minutes per station (can be customized)

            # Prepare response data
            data = {
                "start_station": start_station.name,
                "end_station": end_station.name,
                "ticket_price": ticket_price,
                "number_of_stations": num_stations,
                "estimated_travel_time": travel_time,
            }
            return Response(data)

        except Exception as e:
            return Response({"error": str(e)}, status=400)


class NearestStationView(APIView):
    """
    Finds the nearest station to the user's location.
    """

    permission_classes = [AllowAny]  # Public access

    def get(self, request):
        try:
            latitude = request.query_params.get("latitude")
            longitude = request.query_params.get("longitude")

            if not latitude or not longitude:
                return Response(
                    {"error": "Latitude and Longitude are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            latitude, longitude = float(latitude), float(longitude)
            nearest_station, distance = find_nearest_station(latitude, longitude)

            if nearest_station is None:
                return Response(
                    {"error": "No stations available."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response(
                {
                    "nearest_station": nearest_station.name,
                    "distance": round(distance, 2),
                }
            )
        except ValueError:
            return Response(
                {"error": "Invalid Latitude or Longitude."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        """
        Handle POST request for nearest station based on latitude and longitude.
        """
        try:
            # Extract latitude and longitude from the request body (JSON)
            latitude = request.data.get("latitude")
            longitude = request.data.get("longitude")

            if not latitude or not longitude:
                return Response(
                    {"error": "Latitude and Longitude are required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            latitude, longitude = float(latitude), float(longitude)
            nearest_station, distance = find_nearest_station(latitude, longitude)

            if nearest_station is None:
                return Response(
                    {"error": "No stations available."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            return Response(
                {
                    "nearest_station": nearest_station.name,
                    "distance": round(distance, 2),
                }
            )
        except ValueError:
            return Response(
                {"error": "Invalid Latitude or Longitude."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
