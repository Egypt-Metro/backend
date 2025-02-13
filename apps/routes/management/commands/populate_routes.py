# apps/routes/management/commands/populate_routes.py

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.stations.models import Station
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
            total_stations = stations.count()
            total_routes = total_stations * (total_stations - 1)  # n * (n-1) possible routes

            self.stdout.write(
                f'Found {total_stations} stations. Will calculate {total_routes} routes...'
            )

            routes_created = 0
            routes_skipped = 0
            routes_failed = 0

            with transaction.atomic():
                # Create progress bar
                progress_bar = tqdm(total=total_routes, desc="Calculating routes")

                for start_station in stations:
                    for end_station in stations:
                        if start_station != end_station:
                            try:
                                # Check if route already exists
                                existing_route = Route.objects.filter(
                                    start_station=start_station,
                                    end_station=end_station,
                                    is_active=True
                                ).first()

                                if existing_route:
                                    routes_skipped += 1
                                    progress_bar.update(1)
                                    continue

                                # Calculate route
                                route_data = route_service.find_route(
                                    start_station.id,
                                    end_station.id
                                )

                                if route_data:
                                    # Create route
                                    Route.objects.create(
                                        start_station=start_station,
                                        end_station=end_station,
                                        total_distance=route_data['distance'],
                                        total_time=route_data['distance'] / 833.33,
                                        path=route_data['path'],
                                        interchanges=route_data['interchanges'],
                                        is_active=True
                                    )
                                    routes_created += 1

                                    if routes_created % 100 == 0:
                                        self.stdout.write(
                                            f'Progress: {routes_created}/{total_routes} routes created'
                                        )
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

        except Exception as e:
            logger.error(f'Error populating routes: {str(e)}')
            self.stdout.write(
                self.style.ERROR(f'Error populating routes: {str(e)}')
            )
