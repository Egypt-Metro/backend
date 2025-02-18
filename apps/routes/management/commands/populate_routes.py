from typing import Dict, List, Tuple
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.stations.models import Line, LineStation, Station
from apps.routes.models import Route
from apps.routes.services.route_service import MetroRouteService
import logging
from tqdm import tqdm
from django.db.models import Prefetch
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Populate all possible routes between stations"
    batch_size = 2000
    chunk_size = 500

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size",
            type=int,
            default=self.batch_size,
            help="Batch size for route population",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Clear existing routes before populating",
        )
        parser.add_argument(
            "--workers",
            type=int,
            default=4,
            help="Number of worker threads",
        )

    def handle(self, *args, **options):
        try:
            stats = {"created": 0, "skipped": 0, "failed": 0, "total": 0}

            if options["clear"]:
                self.clear_existing_routes()

            stations = self.get_ordered_stations()
            existing_routes = self.get_existing_routes()

            # Create station pairs using IDs instead of objects
            station_pairs = self.create_station_pairs(stations)
            chunks = self.create_chunks(station_pairs, self.chunk_size)

            total_chunks = len(chunks)
            with tqdm(total=total_chunks, desc="Processing chunks") as pbar:
                with ThreadPoolExecutor(max_workers=options["workers"]) as executor:
                    futures = []
                    for chunk in chunks:
                        future = executor.submit(
                            self.process_chunk,
                            chunk,
                            existing_routes
                        )
                        futures.append(future)

                    for future in futures:
                        try:
                            result = future.result()
                            if result:
                                self.save_routes_batch(result)
                                stats["created"] += len(result)
                            pbar.update(1)
                        except Exception as e:
                            logger.error(f"Chunk processing failed: {str(e)}")
                            stats["failed"] += 1
                            pbar.update(1)

            self.print_summary(stats)

        except Exception as e:
            logger.error(f"Route population failed: {str(e)}")
            self.stdout.write(self.style.ERROR(f"Route population failed: {str(e)}"))

    def create_chunks(self, items: list, chunk_size: int) -> List[list]:
        return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]

    def create_station_pairs(self, stations: List[Station]) -> List[Tuple[int, int, str, str]]:
        pairs = []
        for i, start_station in enumerate(stations):
            for end_station in stations[i + 1:]:
                pairs.append((
                    start_station.id,
                    end_station.id,
                    start_station.name,
                    end_station.name
                ))
        return pairs

    def calculate_routes(self, stations: List[Station], batch_size: int, stats: Dict):
        """Calculate routes between stations"""
        route_service = MetroRouteService()
        current_batch = []
        total_routes = len(stations) * (len(stations) - 1)  # Both directions

        with tqdm(total=total_routes, desc="Calculating routes") as progress_bar:
            for start_station in stations:
                for end_station in stations:
                    if start_station.id == end_station.id:
                        continue  # Skip same station

                    try:
                        # Create route in both directions
                        route_data = route_service.find_route(
                            start_station.id, end_station.id
                        )

                        if route_data:
                            current_batch.append({
                                "start_station": start_station,
                                "end_station": end_station,
                                "route_data": route_data,
                                "total_time": self.calculate_total_time(route_data),
                            })

                            # Create reverse route if it doesn't exist
                            reverse_route_data = route_service.find_route(
                                end_station.id, start_station.id
                            )
                            if reverse_route_data:
                                current_batch.append({
                                    "start_station": end_station,
                                    "end_station": start_station,
                                    "route_data": reverse_route_data,
                                    "total_time": self.calculate_total_time(reverse_route_data),
                                })

                        if len(current_batch) >= batch_size:
                            self.save_batch_with_retry(current_batch)
                            current_batch = []

                    except Exception as e:
                        self.handle_route_error(start_station, end_station, e, stats)

                    progress_bar.update(1)

            if current_batch:
                self.save_batch_with_retry(current_batch)

    def process_chunk(self, chunk: List[Tuple[int, int, str, str]], existing_routes: set) -> List[Dict]:
        route_service = MetroRouteService()
        routes_batch = []

        for start_id, end_id, start_name, end_name in chunk:
            if (start_id, end_id) in existing_routes:
                continue

            try:
                route_data = route_service.find_route(start_id, end_id)

                if route_data:
                    routes_batch.append({
                        "start_station_id": start_id,
                        "end_station_id": end_id,
                        "distance": route_data["distance"],
                        "total_time": self.calculate_total_time(route_data),
                        "path": route_data["path"],
                        "interchanges": route_data["interchanges"],
                    })
                else:
                    logger.warning(f"No route data found for {start_name} -> {end_name}")

            except Exception as e:
                logger.error(
                    f"Route calculation failed: {start_name} (ID: {start_id}) -> {end_name} (ID: {end_id}): {str(e)}"
                )

        return routes_batch

    @transaction.atomic
    def save_routes_batch(self, routes_data: List[Dict]):
        routes_to_create = []
        for route_info in routes_data:
            start_station = Station.objects.get(id=route_info["start_station_id"])
            end_station = Station.objects.get(id=route_info["end_station_id"])

            routes_to_create.append(
                Route(
                    start_station=start_station,
                    end_station=end_station,
                    total_distance=route_info["distance"],
                    total_time=route_info["total_time"],
                    path=route_info["path"],
                    interchanges=route_info["interchanges"],
                    is_active=True,
                )
            )

        Route.objects.bulk_create(
            routes_to_create,
            batch_size=self.batch_size,
            ignore_conflicts=True
        )

    def get_ordered_stations(self) -> List[Station]:
        stations = []
        seen_stations = set()

        lines = Line.objects.prefetch_related(
            Prefetch(
                "line_stations",
                queryset=LineStation.objects.select_related("station").order_by("order"),
            )
        ).all()

        for line in lines:
            for line_station in line.line_stations.all():
                if line_station.station.id not in seen_stations:
                    stations.append(line_station.station)
                    seen_stations.add(line_station.station.id)

        total_stations = len(stations)
        total_routes = (total_stations * (total_stations - 1)) // 2
        self.stdout.write(
            f"Found {total_stations} stations. Will calculate {total_routes} routes."
        )
        return stations

    def get_existing_routes(self) -> set:
        return set(
            Route.objects.filter(is_active=True).values_list(
                "start_station_id", "end_station_id"
            )
        )

    def clear_existing_routes(self):
        self.stdout.write("Clearing existing routes...")
        try:
            with transaction.atomic():
                Route.objects.all().delete()
                self.stdout.write(self.style.SUCCESS("Successfully cleared existing routes"))
        except Exception as e:
            logger.error(f"Failed to clear routes: {str(e)}")
            raise

    def calculate_total_time(self, route_data: Dict) -> int:
        return (
            route_data["num_stations"] * 2  # Base time
            + len(route_data["interchanges"]) * 3  # Interchange time
        )

    def print_summary(self, stats: Dict):
        self.stdout.write(
            self.style.SUCCESS(
                f"\nRoute population completed:\n"
                f'Created: {stats["created"]}\n'
                f'Skipped: {stats["skipped"]}\n'
                f'Failed: {stats["failed"]}\n'
                f'Total: {stats["created"] + stats["skipped"] + stats["failed"]}'
            )
        )
