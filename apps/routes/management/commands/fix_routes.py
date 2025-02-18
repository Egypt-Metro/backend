# apps/routes/management/commands/fix_routes.py

from django.core.management.base import BaseCommand
from apps.routes.models import Route
from apps.stations.models import Line
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fix route data (number of stations and primary line)'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                routes = Route.objects.all()
                total = routes.count()
                updated = 0

                self.stdout.write(f"Found {total} routes to process")

                for route in routes:
                    try:
                        # Fix number of stations
                        if route.path:
                            route.number_of_stations = len([
                                station for station in route.path
                                if isinstance(station, dict) and 'station' in station
                            ])

                        # Fix primary line
                        if route.path and isinstance(route.path, list) and len(route.path) > 0:
                            first_segment = route.path[0]
                            if isinstance(first_segment, dict) and 'line' in first_segment:
                                try:
                                    route.primary_line = Line.objects.get(
                                        name=first_segment['line']
                                    )
                                except Line.DoesNotExist:
                                    logger.warning(
                                        f"Line not found: {first_segment['line']}"
                                    )
                                    route.primary_line = None

                        route.save()
                        updated += 1

                        if updated % 100 == 0:
                            self.stdout.write(
                                f"Processed {updated}/{total} routes"
                            )

                    except Exception as e:
                        logger.error(
                            f"Error processing route {route.id}: {str(e)}"
                        )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully updated {updated} routes"
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to fix routes: {str(e)}")
            )
