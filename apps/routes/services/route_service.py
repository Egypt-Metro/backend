import heapq
import logging
from collections import deque
from apps.routes.services.graph_service import GraphService

logger = logging.getLogger(__name__)


class RouteService:
    """
    Service for computing the shortest path and ensuring all stations are connected.
    """

    def __init__(self):
        self.graph = GraphService.build_graph()

    def _bfs_connected_component(self, start_station):
        """
        Performs BFS to find all stations connected to the given start station.
        """
        visited = set()
        queue = deque([start_station])

        while queue:
            station = queue.popleft()
            if station not in visited:
                visited.add(station)
                queue.extend(neighbor for neighbor, _ in self.graph.get(station, []))

        return visited

    def ensure_all_stations_connected(self):
        """
        Ensures all stations are part of a single connected component.
        If not, adds the minimum number of edges to connect them.
        """
        stations = set(self.graph.keys())
        if not stations:
            return  # No stations in the graph

        # Find all connected components
        components = []
        visited = set()

        for station in stations:
            if station not in visited:
                component = self._bfs_connected_component(station)
                components.append(component)
                visited.update(component)

        if len(components) == 1:
            logger.info("All stations are already connected.")
            return  # The graph is already fully connected

        # Add minimum edges to connect components
        logger.warning(f"Graph is disconnected! Found {len(components)} separate groups.")

        new_connections = []
        for i in range(len(components) - 1):
            # Pick any station from the current component and connect it to another component
            station1 = next(iter(components[i]))
            station2 = next(iter(components[i + 1]))

            # Add a bidirectional edge with weight 1 (default)
            self.graph[station1].append((station2, 1))
            self.graph[station2].append((station1, 1))
            new_connections.append((station1, station2))

        logger.info(f"Added {len(new_connections)} new connections to merge all components.")
        return new_connections

    def find_shortest_path(self, start_station_id, end_station_id):
        """
        Implements Dijkstra's algorithm to find the shortest path between two stations.
        """
        if start_station_id not in self.graph or end_station_id not in self.graph:
            logger.error(f"Invalid station IDs: {start_station_id}, {end_station_id}")
            raise ValueError("One or both station IDs are invalid.")

        if start_station_id == end_station_id:
            return {"distance": 0, "path": [start_station_id]}

        # Initialize distances and priority queue
        distances = {station_id: float("inf") for station_id in self.graph}
        previous_stations = {station_id: None for station_id in self.graph}
        distances[start_station_id] = 0
        priority_queue = [(0, start_station_id)]

        while priority_queue:
            current_distance, current_station = heapq.heappop(priority_queue)

            if current_station == end_station_id:
                break

            if current_distance > distances[current_station]:
                continue

            for neighbor, weight in self.graph[current_station]:
                distance = current_distance + weight
                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous_stations[neighbor] = current_station
                    heapq.heappush(priority_queue, (distance, neighbor))

        # Reconstruct the shortest path
        path = []
        current_id = end_station_id
        while current_id is not None:
            path.insert(0, current_id)
            current_id = previous_stations[current_id]

        if path[0] != start_station_id:
            logger.error(f"No valid path found from {start_station_id} to {end_station_id}")
            return None

        return {
            "distance": distances[end_station_id] if distances[end_station_id] != float("inf") else None,
            "path": path
        }

    def bfs_shortest_path(self, start_station_id, end_station_id):
        """
        Implements BFS to find the shortest path in an unweighted graph.
        """
        if start_station_id not in self.graph or end_station_id not in self.graph:
            logger.error(f"Invalid station IDs: {start_station_id}, {end_station_id}")
            raise ValueError("One or both station IDs are invalid.")

        if start_station_id == end_station_id:
            return [start_station_id]

        queue = deque([(start_station_id, [])])
        visited = set()

        while queue:
            current_station, path = queue.popleft()

            if current_station in visited:
                continue
            visited.add(current_station)

            if current_station == end_station_id:
                path.append(current_station)
                return path

            for neighbor, _ in self.graph.get(current_station, []):
                queue.append((neighbor, path + [current_station]))

        logger.warning(f"No path found from {start_station_id} to {end_station_id}")
        return None
