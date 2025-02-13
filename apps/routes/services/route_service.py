# apps/routes/services/route_service.py

from typing import Dict, List, Optional
from collections import defaultdict
import heapq
from apps.stations.models import Station, LineStation
from .cache_service import CacheService


class MetroRouteService:
    def __init__(self):
        self.graph = defaultdict(dict)
        self.station_lines = defaultdict(set)
        self.cache_service = CacheService()
        self.build_graph()

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

    def _connect_sequential_stations(self, line_stations: List[LineStation]):
        """Connect sequential stations on the same line"""
        for i in range(len(line_stations) - 1):
            current = line_stations[i]
            next_station = line_stations[i + 1]
            distance = current.station.distance_to(next_station.station)

            self.graph[current.station.id][next_station.station.id] = {
                'distance': distance,
                'line_id': current.line.id,
                'line_name': current.line.name,
                'line_color': current.line.color_code
            }
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
                        distance = Station.objects.get(
                            id=station_id
                        ).distance_to(cs.station)

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
        """Calculate the route between two stations"""
        if start_id not in self.graph or end_id not in self.graph:
            return None

        distances = {station_id: float('infinity') for station_id in self.graph}
        distances[start_id] = 0
        previous = {}
        lines_used = {}
        pq = [(0, start_id)]

        while pq:
            current_distance, current = heapq.heappop(pq)

            if current == end_id:
                break

            if current_distance > distances[current]:
                continue

            for neighbor, edge_data in self.graph[current].items():
                distance = current_distance + edge_data['distance']

                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current
                    lines_used[neighbor] = {
                        'line_id': edge_data['line_id'],
                        'line_name': edge_data['line_name'],
                        'line_color': edge_data['line_color']
                    }
                    heapq.heappush(pq, (distance, neighbor))

        if end_id not in previous:
            return None

        # Reconstruct path
        path = []
        current = end_id
        line_changes = []
        current_line = None

        while current in previous:
            station = Station.objects.get(id=current)
            line_info = lines_used[current]

            if current_line and current_line != line_info['line_id']:
                line_changes.append({
                    'station': station.name,
                    'from_line': current_line,
                    'to_line': line_info['line_id']
                })

            path.append({
                'station': station.name,
                'line': line_info['line_name'],
                'line_color': line_info['line_color']
            })

            current_line = line_info['line_id']
            current = previous[current]

        # Add start station
        start_station = Station.objects.get(id=start_id)
        if path:  # Check if path exists
            first_station_name = path[0]['station']
            if first_station_name in lines_used:
                first_line_info = lines_used[first_station_name]
                path.append({
                    'station': start_station.name,
                    'line': first_line_info['line_name'],
                    'line_color': first_line_info['line_color']
                })
            else:
                # Handle case where first station info is not in lines_used
                path.append({
                    'station': start_station.name,
                    'line': 'Unknown',
                    'line_color': '#000000'
                })
        path.reverse()

        return {
            'path': path,
            'distance': distances[end_id],
            'interchanges': line_changes,
            'num_stations': len(path)
        }
