# apps/routes/services/route_service.py

from typing import Dict, Optional
from geopy.distance import geodesic
from collections import defaultdict
from apps.stations.models import Line, Station, LineStation
from .cache_service import CacheService


class MetroRouteService:
    def __init__(self):
        self.graph = defaultdict(dict)
        self.station_lines = defaultdict(set)
        self.cache_service = CacheService()
        self.build_graph()

    def _calculate_distance(self, station1: Station, station2: Station) -> float:
        """Calculate the distance between two stations in meters"""
        return geodesic(
            (station1.latitude, station1.longitude),
            (station2.latitude, station2.longitude)
        ).meters

    def build_graph(self):
        """Build an optimized graph representation of the metro network"""
        line_stations = LineStation.objects.select_related(
            'station', 'line'
        ).order_by('line', 'order')

        current_line = None
        line_stations_list = []

        for ls in line_stations:
            self.station_lines[ls.station.id].add(ls.line.id)

            if current_line != ls.line:
                if line_stations_list:
                    self._connect_sequential_stations(line_stations_list)
                line_stations_list = []
                current_line = ls.line

            line_stations_list.append(ls)

        if line_stations_list:
            self._connect_sequential_stations(line_stations_list)

        self._add_interchange_connections()

    def _connect_sequential_stations(self, line_stations):
        """Connect sequential stations on the same line"""
        for i in range(len(line_stations) - 1):
            current = line_stations[i]
            next_station = line_stations[i + 1]
            distance = self._calculate_distance(current.station, next_station.station)

            self.graph[current.station.id][next_station.station.id] = {
                'distance': distance,
                'line_id': current.line.id,
                'line_name': current.line.name,
                'line_color': current.line.color_code
            }
            # Add reverse connection for bidirectional travel
            self.graph[next_station.station.id][current.station.id] = {
                'distance': distance,
                'line_id': current.line.id,
                'line_name': current.line.name,
                'line_color': current.line.color_code
            }

    def _add_interchange_connections(self):
        """Add connections between stations that share multiple lines"""
        for station_id, lines in self.station_lines.items():
            if len(lines) > 1:
                connected_stations = LineStation.objects.filter(
                    line_id__in=lines
                ).exclude(
                    station_id=station_id
                ).select_related('station', 'line')

                for cs in connected_stations:
                    if station_id not in self.graph[cs.station.id]:
                        station = Station.objects.get(id=station_id)
                        distance = self._calculate_distance(station, cs.station)

                        self.graph[station_id][cs.station.id] = {
                            'distance': distance,
                            'line_id': cs.line.id,
                            'line_name': cs.line.name,
                            'line_color': cs.line.color_code
                        }

    def find_route(self, start_id: int, end_id: int) -> Optional[Dict]:
        """Find the optimal route between two stations"""
        # Try to get from cache first
        cached_route = self.cache_service.get_cached_route(start_id, end_id)
        if cached_route:
            return cached_route

        # Calculate new route
        route_data = self._calculate_route(start_id, end_id)

        # Cache the route if it exists
        if route_data:
            self.cache_service.cache_route(start_id, end_id, route_data)

        return route_data

    def _calculate_route(self, start_id: int, end_id: int) -> Optional[Dict]:
        """Calculate optimal route considering interchanges"""
        if start_id not in self.graph or end_id not in self.graph:
            return None

        start_station = Station.objects.get(id=start_id)
        end_station = Station.objects.get(id=end_id)

        # Check if stations are on the same line
        common_lines = set(start_station.lines.all()) & set(end_station.lines.all())
        if common_lines:
            # Direct route
            line = common_lines.pop()
            return self._get_direct_route(start_station, end_station, line)

        # Need to find route with interchange
        return self._get_route_with_interchange(start_station, end_station)

    def _get_direct_route(self, start_station: Station, end_station: Station, line: Line) -> Dict:
        """Calculate direct route on same line"""
        start_order = start_station.get_station_order(line)
        end_order = end_station.get_station_order(line)

        # Get all stations in order
        stations = []
        if start_order < end_order:
            for order in range(start_order, end_order + 1):
                station = Station.objects.get(
                    station_lines__line=line,
                    station_lines__order=order
                )
                stations.append({
                    'station': station.name,
                    'line': line.name,
                    'line_color': line.color_code
                })
        else:
            for order in range(start_order, end_order - 1, -1):
                station = Station.objects.get(
                    station_lines__line=line,
                    station_lines__order=order
                )
                stations.append({
                    'station': station.name,
                    'line': line.name,
                    'line_color': line.color_code
                })

        return {
            'path': stations,
            'distance': start_station.distance_to(end_station),
            'num_stations': len(stations),
            'interchanges': []
        }

    def _get_route_with_interchange(self, start_station: Station, end_station: Station) -> Dict:
        """Find best route requiring line changes"""
        best_route = None
        min_total_distance = float('inf')

        # Get all possible interchange combinations
        for start_line in start_station.lines.all():
            for end_line in end_station.lines.all():
                # Find connecting stations between these lines
                connecting_stations = Station.objects.filter(
                    lines=start_line
                ).filter(
                    lines=end_line
                ).distinct()

                for interchange in connecting_stations:
                    # Calculate route through this interchange
                    first_segment = self._get_direct_route(
                        start_station,
                        interchange,
                        start_line
                    )
                    second_segment = self._get_direct_route(
                        interchange,
                        end_station,
                        end_line
                    )

                    total_distance = first_segment['distance'] + second_segment['distance']
                    if total_distance < min_total_distance:
                        min_total_distance = total_distance
                        # Combine routes
                        path = first_segment['path'] + second_segment['path'][1:]
                        best_route = {
                            'path': path,
                            'distance': total_distance,
                            'num_stations': len(path),
                            'interchanges': [{
                                'station': interchange.name,
                                'from_line': start_line.name,
                                'to_line': end_line.name
                            }]
                        }

        return best_route
