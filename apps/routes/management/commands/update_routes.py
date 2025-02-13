# apps/routes/management/commands/update_routes.py

from django.core.management.base import BaseCommand
from apps.routes.models import Route
from apps.routes.services.route_service import MetroRouteService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Update existing routes'

    def handle(self, *args, **options):
        route_service = MetroRouteService()
        routes = Route.objects.filter(is_active=True)
        updated = 0

        for route in routes:
            route_data = route_service.find_route(
                route.start_station.id,
                route.end_station.id
            )

            if route_data:
                route.total_distance = route_data['distance']
                route.total_time = route_data['distance'] / 833.33
                route.path = route_data['path']
                route.interchanges = route_data['interchanges']
                route.save()
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(f'Successfully updated {updated} routes')
        )
