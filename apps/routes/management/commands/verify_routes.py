from django.core.management.base import BaseCommand
from apps.stations.models import Station, Line
from apps.routes.models import Route
from apps.routes.services.route_service import MetroRouteService
from django.db import transaction
from tqdm import tqdm
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Verify and fix missing routes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Fix missing routes'
        )
        parser.add_argument(
            '--verify-only',
            action='store_true',
            help='Only verify routes without fixing'
        )

    def handle(self, *args, **options):
        try:
            # Get all stations
            stations = Station.objects.all().order_by('id')
            total_stations = stations.count()
            expected_routes = total_stations * (total_stations - 1)

            # Get existing routes
            existing_routes = set(
                Route.objects.values_list('start_station_id', 'end_station_id')
            )

            # Print verification results
            self.stdout.write("\nRoute Verification Results:")
            self.stdout.write(f"Total stations: {total_stations}")
            self.stdout.write(f"Expected routes: {expected_routes}")
            self.stdout.write(f"Existing routes: {len(existing_routes)}")
            self.stdout.write(f"Missing routes: {expected_routes - len(existing_routes)}")

            # Calculate missing routes percentage
            missing_percentage = ((expected_routes - len(existing_routes)) / expected_routes) * 100
            self.stdout.write(f"Missing routes percentage: {missing_percentage:.2f}%")

            # If verify-only, show detailed analysis and return
            if options['verify_only']:
                self.analyze_routes(stations, existing_routes)
                return

            # Find missing pairs
            if options['fix']:
                missing_pairs = self.find_missing_pairs(stations, existing_routes)
                self.stdout.write(f"\nFound {len(missing_pairs)} missing routes")
                self.create_missing_routes(missing_pairs)

        except Exception as e:
            logger.error(f"Error during route verification: {str(e)}")
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))

    def analyze_routes(self, stations, existing_routes):
        """Analyze existing routes and show detailed information"""
        self.stdout.write("\nDetailed Route Analysis:")

        # Analyze route distribution by line
        line_stats = {}
        for line in Line.objects.all():
            line_routes = Route.objects.filter(
                start_station__lines=line
            ).count()
            line_stats[line.name] = line_routes
            self.stdout.write(f"{line.name}: {line_routes} routes")

        # Find stations with least routes
        station_route_counts = {}
        for station in stations:
            route_count = Route.objects.filter(
                start_station=station
            ).count()
            station_route_counts[station.name] = route_count

        # Show stations with fewest routes
        self.stdout.write("\nStations with fewest routes:")
        sorted_stations = sorted(
            station_route_counts.items(),
            key=lambda x: x[1]
        )
        for station, count in sorted_stations[:10]:
            self.stdout.write(f"{station}: {count} routes")

    def find_missing_pairs(self, stations, existing_routes):
        """Find missing route pairs"""
        missing_pairs = []
        total_pairs = len(stations) * (len(stations) - 1)

        with tqdm(total=total_pairs, desc="Finding missing routes") as pbar:
            for start_station in stations:
                for end_station in stations:
                    if start_station.id != end_station.id:
                        if (start_station.id, end_station.id) not in existing_routes:
                            missing_pairs.append((start_station, end_station))
                    pbar.update(1)

        return missing_pairs

    def create_missing_routes(self, missing_pairs):
        """Create missing routes"""
        route_service = MetroRouteService()
        created_count = 0
        error_count = 0
        error_pairs = []

        with tqdm(total=len(missing_pairs), desc="Creating missing routes") as pbar:
            for start_station, end_station in missing_pairs:
                try:
                    route_data = route_service.find_route(
                        start_station.id,
                        end_station.id
                    )

                    if route_data:
                        with transaction.atomic():
                            Route.objects.create(
                                start_station=start_station,
                                end_station=end_station,
                                total_distance=route_data['distance'],
                                total_time=self.calculate_total_time(route_data),
                                path=route_data['path'],
                                interchanges=route_data['interchanges'],
                                number_of_stations=len(route_data['path']),
                                is_active=True
                            )
                        created_count += 1
                    else:
                        error_pairs.append((start_station.name, end_station.name))
                        error_count += 1

                except Exception as e:
                    logger.error(
                        f"Error creating route {start_station.name} -> {end_station.name}: {str(e)}"
                    )
                    error_pairs.append((start_station.name, end_station.name))
                    error_count += 1

                pbar.update(1)

        # Log failed routes
        self.log_failed_routes(error_pairs)

        # Print summary
        self.stdout.write("\nRoute Creation Summary:")
        self.stdout.write(f"Successfully created: {created_count}")
        self.stdout.write(f"Failed to create: {error_count}")

        if error_pairs:
            self.stdout.write("\nFailed Routes:")
            for start, end in error_pairs[:10]:  # Show first 10 failed routes
                self.stdout.write(f"  {start} -> {end}")
            if len(error_pairs) > 10:
                self.stdout.write(f"  ... and {len(error_pairs) - 10} more")

    def log_failed_routes(self, failed_routes):
        """Log failed routes to a file"""
        with open('failed_routes.log', 'w', encoding='utf-8') as f:
            for start, end in failed_routes:
                f.write(f"{start} -> {end}\n")

    def retry_failed_routes(self):
        """Retry failed routes from the log file"""
        route_service = MetroRouteService()
        with open('failed_routes.log', 'r', encoding='utf-8') as f:
            failed_routes = [line.strip().split(' -> ') for line in f.readlines()]

        for start_name, end_name in failed_routes:
            try:
                start_station = Station.objects.get(name=start_name)
                end_station = Station.objects.get(name=end_name)

                route_data = route_service.find_route(
                    start_station.id,
                    end_station.id
                )

                if route_data:
                    with transaction.atomic():
                        Route.objects.create(
                            start_station=start_station,
                            end_station=end_station,
                            total_distance=route_data['distance'],
                            total_time=self.calculate_total_time(route_data),
                            path=route_data['path'],
                            interchanges=route_data['interchanges'],
                            is_active=True
                        )
                    logger.info(f"Successfully retried route: {start_name} -> {end_name}")
                else:
                    logger.warning(f"No route data found for {start_name} -> {end_name}")

            except Exception as e:
                logger.error(f"Failed to retry route: {start_name} -> {end_name}: {str(e)}")

    def calculate_total_time(self, route_data):
        """Calculate total travel time"""
        return (
            route_data['num_stations'] * 2  # Base time
            + len(route_data['interchanges']) * 3  # Interchange time
        )
