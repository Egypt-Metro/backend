# apps/trains/management/commands/reset_trains_tables.py

from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings
import os
import glob


class Command(BaseCommand):
    help = 'Reset trains tables and recreate them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt'
        )

    def handle(self, *args, **options):
        if not options['force']:
            self.stdout.write(
                self.style.WARNING(
                    '\nWARNING: This will:\n'
                    '1. Delete all trains migrations\n'
                    '2. Drop these tables:\n'
                    '   - trains_train\n'
                    '   - trains_traincar\n'
                    '   - trains_schedule\n'
                    '\nAre you sure? [y/N]: '
                )
            )
            if input().lower() != 'y':
                self.stdout.write(self.style.NOTICE('Operation cancelled.'))
                return

        try:
            # 1. Delete migration files
            migrations_dir = os.path.join(settings.BASE_DIR, 'apps', 'trains', 'migrations')
            for file in glob.glob(os.path.join(migrations_dir, '0*.py')):
                os.remove(file)
                self.stdout.write(f'Deleted migration: {os.path.basename(file)}')

            # 2. Drop all existing trains tables
            with connection.cursor() as cursor:
                cursor.execute("""
                    DO $$ 
                    BEGIN
                        DROP TABLE IF EXISTS trains_schedule CASCADE;
                        DROP TABLE IF EXISTS trains_traincar CASCADE;
                        DROP TABLE IF EXISTS trains_train CASCADE;
                    END $$;
                """)

            # 3. Create new migrations
            from django.core.management import call_command
            call_command('makemigrations', 'trains')

            # 4. Apply migrations
            call_command('migrate', 'trains')

            # 5. Verify tables
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name LIKE 'trains_%'
                """)
                tables = cursor.fetchall()
                
                self.stdout.write('\nCreated tables:')
                for table in tables:
                    self.stdout.write(f'- {table[0]}')

            self.stdout.write(self.style.SUCCESS('\nSuccessfully reset trains tables'))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )
            raise