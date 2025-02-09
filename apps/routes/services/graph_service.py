from collections import defaultdict
from venv import logger
from apps.stations.models import LineStation, Interchange


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
        - Edges are connections between adjacent stations in the same line or through interchanges.
        """
        if cls._graph is None:
            cls._graph = defaultdict(list)
            line_stations = LineStation.objects.select_related("station", "line").order_by("order")

            # Group stations by line
            line_to_stations = defaultdict(list)
            for line_station in line_stations:
                line_to_stations[line_station.line.id].append(line_station.station.id)

            # Build graph with connections between adjacent stations in the same line
            for line_id, station_ids in line_to_stations.items():
                for i in range(len(station_ids) - 1):
                    current_station = station_ids[i]
                    next_station = station_ids[i + 1]
                    cls._graph[current_station].append((next_station, 1))  # Default weight of 1
                    cls._graph[next_station].append((current_station, 1))  # Bidirectional

            # Add connections between stations that share the same interchange
            interchanges = Interchange.objects.select_related("station").prefetch_related("connected_stations")
            for interchange in interchanges:
                station_id = interchange.station.id
                for connected_station in interchange.connected_stations.all():
                    cls._graph[station_id].append((connected_station.id, 1))  # Default weight of 1
                    cls._graph[connected_station.id].append((station_id, 1))  # Bidirectional

            # Log the graph structure for debugging
            logger.info("Graph structure:")
            for station_id, neighbors in cls._graph.items():
                logger.info(f"Station {station_id} -> {neighbors}")

        return cls._graph
