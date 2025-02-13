# apps/routes/management/commands/cleanup_routes.py

from django.core.management.base import BaseCommand
from django.db import connection
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Cleans up PrecomputedRoute model and related data'

    def handle(self, *args, **options):
        self.stdout.write('Starting cleanup process...')

        # Clear cache first
        self.stdout.write('Clearing cache...')
        cache.clear()

        # Drop PrecomputedRoute table and related objects
        with connection.cursor() as cursor:
            self.stdout.write('Removing PrecomputedRoute data...')

            try:
                # Drop unique constraints first
                cursor.execute("""
                    SELECT constraint_name
                    FROM information_schema.table_constraints
                    WHERE table_name = 'routes_precomputedroute'
                    AND constraint_type = 'UNIQUE'
                """)
                unique_constraints = cursor.fetchall()

                for (constraint,) in unique_constraints:
                    cursor.execute(f'ALTER TABLE routes_precomputedroute DROP CONSTRAINT IF EXISTS "{constraint}"')

                # Drop foreign key constraints
                cursor.execute("""
                    SELECT tc.constraint_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.constraint_column_usage ccu
                    ON tc.constraint_name = ccu.constraint_name
                    WHERE tc.table_name = 'routes_precomputedroute'
                    AND tc.constraint_type = 'FOREIGN KEY'
                """)
                fk_constraints = cursor.fetchall()

                for (constraint,) in fk_constraints:
                    cursor.execute(f'ALTER TABLE routes_precomputedroute DROP CONSTRAINT IF EXISTS "{constraint}"')

                # Drop the table with CASCADE
                cursor.execute('DROP TABLE IF EXISTS routes_precomputedroute CASCADE')

                # Remove any related Django migrations
                cursor.execute("""
                    DELETE FROM django_migrations
                    WHERE app = 'routes'
                    AND name LIKE '%precomputedroute%'
                """)

                self.stdout.write(self.style.SUCCESS('Successfully cleaned up PrecomputedRoute data'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error during cleanup: {str(e)}'))
                logger.error(f'Cleanup error: {str(e)}')
                raise
