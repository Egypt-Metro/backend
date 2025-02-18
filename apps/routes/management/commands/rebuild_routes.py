# apps/routes/management/commands/rebuild_routes.py

from cmath import e
import time
import datetime
from tqdm import tqdm
from django.core.management.base import BaseCommand
from apps.stations.models import Station, Line
from apps.routes.models import Route
from apps.routes.services.route_service import MetroRouteService
from django.db import transaction, connection
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Rebuild all routes between stations'
    chunk_size = 50  # Reduced chunk size
    max_workers = 3  # Reduced workers

    def add_arguments(self, parser):
        parser.add_argument(
            '--workers',
            type=int,
            default=self.max_workers,
            help='Number of worker threads'
        )
        parser.add_argument(
            '--chunk-size',
            type=int,
            default=self.chunk_size,
            help='Size of chunks to process'
        )

    def handle(self, *args, **options):
        try:
            # Initial setup
            initial_count = Route.objects.count()
            start_time = time.time()

            self.stdout.write(f"Initial routes: {initial_count}")

            # Clear existing routes
            self.clear_existing_routes()

            # Get stations and create pairs
            stations = Station.objects.all().order_by('id')
            total_stations = stations.count()
            total_pairs = total_stations * (total_stations - 1)

            self.stdout.write(f"""
Route Creation Plan:
------------------
Total stations: {total_stations}
Expected routes: {total_pairs}
Workers: {options['workers']}
Chunk size: {options['chunk_size']}
            """)

            # Process routes
            created_routes, failed_routes = self.process_routes(
                stations,
                options['workers'],
                options['chunk_size'],
                total_pairs,
                start_time
            )

            # Print final summary
            self.print_final_summary(
                created_routes,
                failed_routes,
                total_pairs,
                start_time
            )

        except Exception:
            logger.error(f"Error rebuilding routes: {str(e)}")
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))

    def clear_existing_routes(self):
        """Clear all existing routes"""
        self.stdout.write("Clearing existing routes...")
        with transaction.atomic():
            Route.objects.all().delete()

    def process_routes(self, stations, num_workers, chunk_size, total_pairs, start_time):
        """Process all routes with progress tracking"""
        station_pairs = self.create_station_pairs(stations)
        chunks = [station_pairs[i:i + chunk_size]
                  for i in range(0, len(station_pairs), chunk_size)]

        created_routes = 0
        failed_routes = []

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            for chunk in chunks:
                futures.append(executor.submit(self.process_chunk, chunk))

            with tqdm(total=total_pairs, desc="Creating routes") as pbar:
                for future in futures:
                    try:
                        result = future.result()
                        created_routes += result['created']
                        failed_routes.extend(result['failed'])

                        # Update progress
                        pbar.update(result['created'])
                        self.show_progress_update(
                            created_routes,
                            failed_routes,
                            total_pairs,
                            start_time
                        )
                    except Exception:
                        logger.error(f"Chunk processing failed: {str(e)}")

        return created_routes, failed_routes

    def create_station_pairs(self, stations):
        """Create all possible station pairs"""
        pairs = []
        for start_station in stations:
            for end_station in stations:
                if start_station.id != end_station.id:
                    pairs.append((start_station, end_station))
        return pairs

    def process_chunk(self, chunk):
        """Process a chunk of station pairs"""
        route_service = MetroRouteService()
        created = 0
        failed = []
        routes_to_create = []

        for start_station, end_station in chunk:
            try:
                # Refresh connection
                connection.close()
                connection.connect()

                route_data = route_service.find_route(
                    start_station.id,
                    end_station.id
                )

                if route_data:
                    routes_to_create.append({
                        'start_station': start_station,
                        'end_station': end_station,
                        'route_data': route_data
                    })
                    created += 1

                    if len(routes_to_create) >= 10:  # Save in very small batches
                        self.save_batch(routes_to_create)
                        routes_to_create = []
                else:
                    failed.append((
                        start_station.name,
                        end_station.name,
                        "No route found"
                    ))

            except Exception:
                logger.error(f"Error processing route from {start_station.name} to {end_station.name}", exc_info=True)
                failed.append((
                    start_station.name,
                    end_station.name,
                    "Exception occurred"
                ))

        # Save remaining routes
        if routes_to_create:
            self.save_batch(routes_to_create)

        return {'created': created, 'failed': failed}

    def save_batch(self, routes_data):
        """Save a batch of routes with retry logic"""
        for attempt in range(3):  # 3 retries
            try:
                with transaction.atomic():
                    Route.objects.bulk_create([
                        Route(
                            start_station=route['start_station'],
                            end_station=route['end_station'],
                            total_distance=route['route_data']['distance'],
                            total_time=self.calculate_total_time(route['route_data']),
                            path=route['route_data']['path'],
                            interchanges=route['route_data']['interchanges'],
                            number_of_stations=len(route['route_data']['path']),
                            primary_line=self.determine_primary_line(route['route_data']),
                            is_active=True
                        )
                        for route in routes_data
                    ], batch_size=10)
                return
            except Exception:
                if attempt == 2:  # Last attempt
                    raise
                connection.close()
                connection.connect()
                time.sleep(1)

    def calculate_total_time(self, route_data):
        """Calculate total travel time"""
        return (
            route_data['num_stations'] * 2 +
            len(route_data['interchanges']) * 3
        )

    def determine_primary_line(self, route_data):
        """Determine primary line from route data"""
        try:
            if route_data['path'] and len(route_data['path']) > 0:
                first_segment = route_data['path'][0]
                if isinstance(first_segment, dict) and 'line' in first_segment:
                    return Line.objects.get(name=first_segment['line'])
        except Exception as e:
            logger.error(f"Error determining primary line: {str(e)}")
        return None

    def show_progress_update(self, created, failed, total, start_time):
        """Show progress update"""
        elapsed_time = time.time() - start_time
        if elapsed_time > 0:
            routes_per_second = created / elapsed_time
            remaining = total - created
            estimated_remaining = remaining / routes_per_second if routes_per_second > 0 else 0
            
            self.stdout.write(f"""
Progress Update:
--------------
Created: {created}/{total} routes ({(created / total) * 100:.1f}%)
Failed: {len(failed)}
Speed: {routes_per_second:.1f} routes/second
Est. remaining: {datetime.timedelta(seconds=int(estimated_remaining))}
            """)

    def print_final_summary(self, created, failed, total, start_time):
        """Print final summary"""
        elapsed_time = time.time() - start_time
        
        self.stdout.write(f"""
Final Summary:
------------
Total time: {datetime.timedelta(seconds=int(elapsed_time))}
Routes created: {created}
Routes failed: {len(failed)}
Success rate: {(created / total) * 100:.1f}%

Route Distribution:
----------------""")

        for line in Line.objects.all():
            count = Route.objects.filter(primary_line=line).count()
            self.stdout.write(f"{line.name}: {count} routes")
