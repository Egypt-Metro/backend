# apps/stations/services/route_service.py

from collections import defaultdict
import heapq

class RouteService:
    def __init__(self, stations):
        self.stations = stations
        self.graph = self.create_graph()
        self.cached_routes = {}

    def create_graph(self):
        """Create a graph representation of stations with weights."""
        graph = defaultdict(dict)
        for station in self.stations:
            for neighbor, weight in station.get_neighbors():  # Assume weights provided
                graph[station][neighbor] = weight
        return graph

    def find_best_route(self, start_station, end_station):
        """Find the shortest path using Dijkstra's algorithm."""
        if (start_station, end_station) in self.cached_routes:
            return self.cached_routes[(start_station, end_station)]

        distances = {station: float('inf') for station in self.graph}
        previous = {station: None for station in self.graph}
        distances[start_station] = 0
        priority_queue = [(0, start_station)]

        while priority_queue:
            current_distance, current_station = heapq.heappop(priority_queue)

            if current_distance > distances[current_station]:
                continue

            for neighbor, weight in self.graph[current_station].items():
                distance = current_distance + weight
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current_station
                    heapq.heappush(priority_queue, (distance, neighbor))

        # Reconstruct the path
        path = []
        current = end_station
        while current:
            path.append(current)
            current = previous[current]
        path.reverse()

        # Cache the result
        self.cached_routes[(start_station, end_station)] = path
        return path

    def update_graph(self, station, neighbors):
        """Update the graph dynamically."""
        self.graph[station] = neighbors
        self.cached_routes.clear()  # Invalidate cache due to graph changes

    def get_route(self, start_station, end_station):
        """Get the precomputed or dynamically computed route."""
        return self.find_best_route(start_station, end_station)
