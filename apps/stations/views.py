from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse
from stations.models import Station
from .services.route_service import RouteService
from stations.services.ticket_service import calculate_ticket_price
from .utils.location_helpers import find_nearest_station
from geopy.distance import geodesic # type: ignore

# Create your views here.
class TripDetailsView(APIView):
    def get(self, request, start_station_id, end_station_id):
        try:
            # Get stations
            start_station = Station.objects.get(id=start_station_id)
            end_station = Station.objects.get(id=end_station_id)

            # Calculate ticket price using the service
            ticket_price = calculate_ticket_price(start_station, end_station)
            
            # Number of stations between start and end
            num_stations = abs(start_station.get_station_order(start_station.lines.first()) - 
                                end_station.get_station_order(end_station.lines.first())) + 1
            
            # Estimated travel time (in minutes)
            travel_time = num_stations * 2  # 2 minutes per station (can be customized)

            # Prepare response data
            data = {
                "start_station": start_station.name,
                "end_station": end_station.name,
                "ticket_price": ticket_price,
                "number_of_stations": num_stations,
                "estimated_travel_time": travel_time
            }
            return Response(data)
        
        except Exception as e:
            return Response({"error": str(e)}, status=400)
        

class NearestStationView(APIView):
    def get(self, request):
        latitude = request.query_params.get("latitude")
        longitude = request.query_params.get("longitude")

        if not latitude or not longitude:
            return Response({"error": "Latitude and Longitude are required"}, status=400)

        nearest_station, distance = find_nearest_station(float(latitude), float(longitude))
        return Response({
            "nearest_station": nearest_station.name,
            "distance": round(distance, 2),
        })