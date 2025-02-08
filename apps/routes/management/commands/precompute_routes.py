import json
import logging
from concurrent.futures import ThreadPoolExecutor
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.stations.models import Station
from apps.routes.models import PrecomputedRoute
from apps.routes.services.route_service import RouteService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Precompute and store shortest paths in DB & cache."

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=100, help="Batch size for inserts.")
        parser.add_argument("--parallel", action="store_true", help="Enable multi-threading.")

    def handle(self, *args, **kwargs):
        batch_size = kwargs["batch_size"]
        use_parallel = kwargs["parallel"]

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

    def _compute_routes_sequential(self, stations, batch_size):
        routes_to_create = []

        for start_station in stations:
            for end_station in stations:
                if start_station == end_station:
                    continue

                result = RouteService().find_shortest_path(start_station.id, end_station.id)
                if result and result["path"]:
                    route = PrecomputedRoute(
                        start_station=start_station,
                        end_station=end_station,
                        path=result["path"],
                        distance=result["distance"]
                    )
                    routes_to_create.append(route)

                    # Store in cache
                    cache.set(f"route:{start_station.id}:{end_station.id}", json.dumps(result), timeout=None)

                if len(routes_to_create) >= batch_size:
                    self._save_routes(routes_to_create)
                    routes_to_create = []

        if routes_to_create:
            self._save_routes(routes_to_create)

    def _compute_routes_parallel(self, stations, batch_size):
        with ThreadPoolExecutor() as executor:
            executor.map(self._compute_for_station, stations, [stations] * len(stations), [batch_size] * len(stations))

    def _compute_for_station(self, start_station, stations, batch_size):
        routes_to_create = []

        for end_station in stations:
            if start_station == end_station:
                continue

            result = RouteService().find_shortest_path(start_station.id, end_station.id)
            if result and result["path"]:
                route = PrecomputedRoute(
                    start_station=start_station,
                    end_station=end_station,
                    path=result["path"],
                    distance=result["distance"]
                )
                routes_to_create.append(route)

                # Store in cache
                cache.set(f"route:{start_station.id}:{end_station.id}", json.dumps(result), timeout=None)

            if len(routes_to_create) >= batch_size:
                self._save_routes(routes_to_create)
                routes_to_create = []

        if routes_to_create:
            self._save_routes(routes_to_create)

    def _save_routes(self, routes):
        with transaction.atomic():
            PrecomputedRoute.objects.bulk_create(routes, ignore_conflicts=True)
            logger.info(f"Saved {len(routes)} routes in database.")
