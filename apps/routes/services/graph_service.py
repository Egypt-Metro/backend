# apps/routes/services/graph_service.py

from collections import defaultdict
from apps.stations.models import LineStation


class GraphService:
    """
    Service for building and managing the metro system graph.
    """

    _graph = None  # Class-level cache for graph

    @classmethod
    def build_graph(cls):
        """
        Builds a graph representation of the metro system where:
        - Nodes are stations
        - Edges are distances between adjacent stations
        """
        if cls._graph is None:
            cls._graph = defaultdict(list)
            line_stations = LineStation.objects.select_related("station", "line")

            for line_station in line_stations:
                station = line_station.station
                next_station = line_station.line.stations.exclude(id=station.id).first()
                if next_station:
                    distance = station.distance_to(next_station)
                    cls._graph[station.id].append((next_station.id, distance))
                    cls._graph[next_station.id].append((station.id, distance))  # Bidirectional

        return cls._graph
