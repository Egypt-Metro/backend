# apps/routes/management/commands/precompute_routes.py

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from apps.routes.services.graph_service import GraphService
from apps.stations.models import Line, Station
from apps.routes.models import PrecomputedRoute
from apps.routes.services.route_service import RouteService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Precompute and store shortest paths in DB & cache."

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=100, help="Batch size for inserts.")
        parser.add_argument("--parallel", action="store_true", help="Enable multi-threading.")
        parser.add_argument("--delete-old", action="store_true", help="Delete old data before starting.")

    def handle(self, *args, **kwargs):
        batch_size = kwargs["batch_size"]
        use_parallel = kwargs["parallel"]
        delete_old = kwargs["delete_old"]

        # Delete old data if requested
        if delete_old:
            self._delete_old_data()

        # Initialize the graph
        self.graph = GraphService.build_graph()

        stations = list(Station.objects.all())  # Convert to list for faster iteration
        if not stations:
            logger.warning("No stations found. Exiting.")
            return

        self.stdout.write(self.style.SUCCESS(f"Precomputing routes for {len(stations)} stations..."))

        if use_parallel:
            self._compute_routes_parallel(stations, batch_size)
        else:
            self._compute_routes_sequential(stations, batch_size)

        self.stdout.write(self.style.SUCCESS("Route precomputation completed."))
        logger.info("Route precomputation completed.")

    def _delete_old_data(self):
        """Delete all precomputed routes before starting."""
        deleted_count, _ = PrecomputedRoute.objects.all().delete()
        logger.info(f"Deleted {deleted_count} old precomputed routes.")
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted_count} old precomputed routes."))

    def _compute_routes_sequential(self, stations, batch_size):
        routes_to_create = []
        total_stations = len(stations)

        for i in range(0, total_stations, batch_size):
            batch_stations = stations[i:i + batch_size]
            for start_station in batch_stations:
                for end_station in batch_stations:
                    if start_station == end_station:
                        continue

                    # Compute routes for each line
                    for line in start_station.lines.all():
                        result = RouteService().find_shortest_path(start_station.id, end_station.id, line.id)
                        if result and result["path"]:
                            route = PrecomputedRoute(
                                start_station=start_station,
                                end_station=end_station,
                                line=line,
                                path=result["path"],
                                interchanges=result.get("interchanges", None)
                            )
                            routes_to_create.append(route)

                            # Store in cache
                            cache.set(
                                f"route:{start_station.id}:{end_station.id}:{line.id}",
                                json.dumps(result, default=self._serialize_object),
                                timeout=None
                            )

                        if len(routes_to_create) >= batch_size:
                            self._save_routes(routes_to_create)
                            routes_to_create = []

            if routes_to_create:
                self._save_routes(routes_to_create)

    def _compute_routes_parallel(self, stations, batch_size):
        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(self._compute_for_station, start_station, stations, batch_size)
                for start_station in stations
            ]
            for future in futures:
                future.result()  # Wait for all threads to complete

    def _compute_for_station(self, start_station, stations, batch_size):
        routes_to_create = []

        for end_station in stations:
            if start_station == end_station:
                continue

            # Validate station IDs
            if not self._validate_stations(start_station, end_station):
                continue

            # Compute routes for each line
            for line in start_station.lines.all():
                # Log the route being computed
                logger.debug(f"Computing route from {start_station.id} to {end_station.id} on line {line.id}")

                result = RouteService().find_shortest_path(start_station.id, end_station.id, line.id)
                if result and result["path"]:
                    route = PrecomputedRoute(
                        start_station=start_station,
                        end_station=end_station,
                        line=line,
                        path=result["path"],
                        interchanges=result.get("interchanges", None)
                    )
                    routes_to_create.append(route)

                    # Store in cache
                    cache.set(
                        f"route:{start_station.id}:{end_station.id}:{line.id}",
                        json.dumps(result, default=self._serialize_object),
                        timeout=None
                    )

                if len(routes_to_create) >= batch_size:
                    self._save_routes(routes_to_create)
                    routes_to_create = []

        if routes_to_create:
            self._save_routes(routes_to_create)

    def _validate_stations(self, start_station, end_station):
        """
        Validate that both stations exist and belong to the same line.
        """
        if not start_station or not end_station:
            logger.error(f"Invalid stations: {start_station}, {end_station}")
            return False

        if start_station.id not in self.graph or end_station.id not in self.graph:
            logger.error(f"Invalid station IDs: {start_station.id}, {end_station.id}")
            return False

        # Check if the stations share at least one common line
        common_lines = set(self.graph[start_station.id]).intersection(set(self.graph[end_station.id]))
        if not common_lines:
            logger.error(f"No common lines between stations: {start_station.id}, {end_station.id}")
            return False

        return True

    def _save_routes(self, routes):
        """
        Save routes to the database, ensuring no duplicate key violations.
        """
        try:
            with transaction.atomic():
                # Filter out existing routes to avoid duplicates
                existing_routes = PrecomputedRoute.objects.filter(
                    start_station__in=[r.start_station for r in routes],
                    end_station__in=[r.end_station for r in routes],
                    line__in=[r.line for r in routes]
                ).values_list('start_station_id', 'end_station_id', 'line_id')

                existing_routes_set = set(existing_routes)

                routes_to_insert = [
                    route for route in routes
                    if (route.start_station.id, route.end_station.id, route.line.id) not in existing_routes_set
                ]

                if routes_to_insert:
                    PrecomputedRoute.objects.bulk_create(routes_to_insert)
                    logger.info(f"Saved {len(routes_to_insert)} routes in database.")
        except IntegrityError as e:
            logger.error(f"IntegrityError while saving routes: {e}")
            raise

    def _serialize_object(self, obj):
        """Convert non-serializable objects to JSON-safe format."""
        if hasattr(obj, "id"):  # Convert Django model objects to their IDs
            return obj.id
        if isinstance(obj, Line):  # Convert Line objects to a dict representation
            return {"id": obj.id, "name": obj.name}  # Adjust fields as needed
        return str(obj)  # Convert unknown objects to strings
