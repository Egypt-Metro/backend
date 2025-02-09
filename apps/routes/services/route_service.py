import heapq
import logging
from apps.routes.services.graph_service import GraphService
from apps.stations.models import Station

logger = logging.getLogger(__name__)


class RouteService:
    """
    Service for computing the shortest path and ensuring all stations are connected.
    """

    def __init__(self):
        self.graph = GraphService.build_graph()

    def find_shortest_path(self, start_station_id, end_station_id, line_id=None):
        """
        Finds the shortest path between two stations, respecting the order of stations within each line.
        """
        if start_station_id not in self.graph or end_station_id not in self.graph:
            logger.error(f"Invalid station IDs: {start_station_id}, {end_station_id}")
            raise ValueError("One or both station IDs are invalid.")

        if start_station_id == end_station_id:
            return {
                "path": [{"station_id": start_station_id, "station_name": "Same Station", "line_name": "N/A"}],
                "interchanges": []
            }

        # Initialize distances and priority queue
        distances = {station_id: float("inf") for station_id in self.graph}
        previous_stations = {station_id: None for station_id in self.graph}
        distances[start_station_id] = 0
        priority_queue = [(0, start_station_id)]

        logger.info(f"Finding shortest path from {start_station_id} to {end_station_id}")

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

        # Log the computed path
        logger.info(f"Computed path: {path}")

        # Get station and line details for the path
        detailed_path = self._get_detailed_path(path)

        # Track interchanges
        interchanges = self._find_interchanges(path)

        return {
            "path": detailed_path,
            "interchanges": interchanges
        }

    def _find_interchanges(self, path):
        """
        Identifies interchanges (line changes) along the path.
        Returns a list of dictionaries with interchange details.
        """
        interchanges = []
        for i in range(1, len(path)):
            current_station = path[i]
            previous_station = path[i - 1]
            current_lines = set(self._get_lines_for_station(current_station))
            previous_lines = set(self._get_lines_for_station(previous_station))

            # Check for line changes
            if current_lines != previous_lines:
                interchange_station = current_station
                from_line = list(previous_lines)[0]  # Get the first line
                to_line = list(current_lines)[0]  # Get the first line

                # Convert Line objects to dictionaries
                interchanges.append({
                    "station_id": interchange_station,
                    "station_name": Station.objects.get(id=interchange_station).name,
                    "from_line": {"id": from_line.id, "name": from_line.name},
                    "to_line": {"id": to_line.id, "name": to_line.name}
                })

        return interchanges

    def _get_detailed_path(self, path):
        """
        Returns a detailed path with station names and line names.
        """
        # Fetch all stations and their line details in a single query
        stations = Station.objects.filter(id__in=path).prefetch_related('lines')
        station_map = {station.id: station for station in stations}

        detailed_path = []
        for station_id in path:
            station = station_map.get(station_id)
            if not station:
                logger.warning(f"Station with ID {station_id} not found.")
                continue

            line_station = station.lines.first()  # Get the first line associated with the station
            line_name = line_station.name if line_station else "N/A"
            detailed_path.append({
                "station_id": station_id,
                "station_name": station.name,
                "line_name": line_name
            })
        return detailed_path

    def _get_lines_for_station(self, station_id):
        """
        Returns the lines associated with a station.
        """
        from apps.stations.models import Station
        station = Station.objects.get(id=station_id)
        return station.lines.all()
