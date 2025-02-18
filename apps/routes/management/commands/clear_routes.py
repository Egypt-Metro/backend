# apps/routes/management/commands/clear_routes.py

from django.core.management.base import BaseCommand
from apps.routes.models import Route
from django.core.cache import cache
from django.db import transaction


class Command(BaseCommand):
    help = 'Clear all routes and cache'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                # Clear routes
                count = Route.objects.count()
                Route.objects.all().delete()
                # Clear cache
                cache.clear()

                self.stdout.write(
                    self.style.SUCCESS(
                        f"Cleared {count} routes and cache successfully"
                    )
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error: {str(e)}")
            )
