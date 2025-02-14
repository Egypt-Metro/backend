# apps/routes/management/commands/populate_routes.py

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.stations.models import LineStation, Station
from apps.routes.models import Route
from apps.routes.services.route_service import MetroRouteService
import logging
from tqdm import tqdm  # For progress bar

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Populate all possible routes between stations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing routes before populating',
        )

    def handle(self, *args, **options):
        try:
            if options['clear']:
                self.stdout.write('Clearing existing routes...')
                Route.objects.all().delete()

            route_service = MetroRouteService()
            stations = Station.objects.all()

            # Calculate total possible routes
            total_stations = stations.count()
            total_routes = total_stations * (total_stations - 1)

            self.stdout.write(
                f'Found {total_stations} stations. Calculating {total_routes} possible routes...'
            )

            routes_created = 0
            routes_skipped = 0
            routes_failed = 0

            with transaction.atomic():
                progress_bar = tqdm(total=total_routes, desc="Calculating routes")

                for start_station in stations:
                    for end_station in stations:
                        if start_station != end_station:
                            try:
                                # Check existing route
                                existing_route = Route.objects.filter(
                                    start_station=start_station,
                                    end_station=end_station,
                                    is_active=True
                                ).first()

                                if existing_route:
                                    routes_skipped += 1
                                    progress_bar.update(1)
                                    continue

                                # Calculate new route
                                route_data = route_service.find_route(
                                    start_station.id,
                                    end_station.id
                                )

                                if route_data:
                                    # Calculate accurate travel time
                                    base_time = route_data['num_stations'] * 2  # 2 minutes per station
                                    interchange_time = len(route_data['interchanges']) * 3  # 3 minutes per interchange
                                    total_time = base_time + interchange_time

                                    # Create route
                                    Route.objects.create(
                                        start_station=start_station,
                                        end_station=end_station,
                                        total_distance=route_data['distance'],
                                        total_time=total_time,
                                        path=route_data['path'],
                                        interchanges=route_data['interchanges'],
                                        is_active=True
                                    )
                                    routes_created += 1

                                else:
                                    routes_failed += 1
                                    logger.warning(
                                        f"No route found between {start_station.name} "
                                        f"and {end_station.name}"
                                    )

                            except Exception as e:
                                routes_failed += 1
                                logger.error(
                                    f"Error creating route from {start_station.name} "
                                    f"to {end_station.name}: {str(e)}"
                                )

                            progress_bar.update(1)

                progress_bar.close()

            # Final summary
            self.stdout.write(
                self.style.SUCCESS(
                    f'\nRoute population completed:\n'
                    f'- Created: {routes_created}\n'
                    f'- Skipped: {routes_skipped}\n'
                    f'- Failed: {routes_failed}\n'
                    f'- Total processed: {routes_created + routes_skipped + routes_failed}'
                )
            )

            for start_station in stations:
                for end_station in stations:
                    if start_station != end_station:
                        try:
                            route_data = route_service.find_route(
                                start_station.id,
                                end_station.id
                            )

                            if route_data:
                                # Verify route calculations
                                if self.verify_route_calculations(route_data, start_station, end_station):
                                    # Create route
                                    self.create_route(route_data, start_station, end_station)
                                    routes_created += 1
                                else:
                                    routes_failed += 1
                                    logger.error(f"Route verification failed for {start_station.name} to {end_station.name}")
                        except Exception as e:
                            routes_failed += 1
                            logger.error(f"Error verifying or creating route from {start_station.name} to {end_station.name}: {str(e)}")

        except Exception as e:
            logger.error(f'Error populating routes: {str(e)}')
            self.stdout.write(
                self.style.ERROR(f'Error populating routes: {str(e)}')
            )

    def monitor_route_creation(self, route_data, start_station, end_station):
        """Monitor and log route creation details"""
        logger.info(f"Creating route: {start_station.name} → {end_station.name}")
        logger.info(f"Distance: {route_data['distance']:.2f}m")
        logger.info(f"Stations: {route_data['num_stations']}")
        if route_data['interchanges']:
            logger.info(f"Interchanges: {len(route_data['interchanges'])}")
            for interchange in route_data['interchanges']:
                logger.info(f"  - {interchange['station']}: "
                            f"{interchange['from_line']} → {interchange['to_line']}")

    def cleanup_old_routes(self):
        """Clean up old or invalid routes"""
        old_routes = Route.objects.filter(is_active=False)
        count = old_routes.count()
        old_routes.delete()
        logger.info(f"Cleaned up {count} old routes")

    def verify_route_calculations(self, route_data, start_station, end_station):
        """Verify route calculations are correct"""
        try:
            # Verify basic route data
            if not route_data or 'path' not in route_data:
                raise ValueError("Invalid route data")

            path = route_data['path']

            # Verify path starts and ends at correct stations
            if path[0]['station'] != start_station.name or path[-1]['station'] != end_station.name:
                raise ValueError("Route path endpoints mismatch")

            # Verify station sequence is continuous
            for i in range(len(path) - 1):
                current = path[i]
                next_station = path[i + 1]

                # Verify stations are connected
                if not self.are_stations_connected(current['station'], next_station['station']):
                    raise ValueError(f"Discontinuous path between {current['station']} and {next_station['station']}")

            # Verify interchanges
            if route_data['interchanges']:
                for interchange in route_data['interchanges']:
                    if not self.is_valid_interchange(interchange['station']):
                        raise ValueError(f"Invalid interchange station: {interchange['station']}")

            return True

        except Exception as e:
            logger.error(f"Route verification failed: {str(e)}")
            return False

    def are_stations_connected(self, station1_name: str, station2_name: str) -> bool:
        """Check if two stations are directly connected"""
        try:
            station1 = Station.objects.get(name=station1_name)
            station2 = Station.objects.get(name=station2_name)

            # Check if stations are on same line and adjacent
            common_lines = set(station1.lines.all()) & set(station2.lines.all())
            for line in common_lines:
                order1 = LineStation.objects.get(line=line, station=station1).order
                order2 = LineStation.objects.get(line=line, station=station2).order
                if abs(order1 - order2) == 1:
                    return True

            return False
        except Exception as e:
            logger.error(f"Error checking station connection: {str(e)}")
            return False

    def is_valid_interchange(self, station_name: str) -> bool:
        """Verify if a station is a valid interchange point"""
        return any(conn["name"] == station_name for conn in self.CONNECTING_STATIONS)
