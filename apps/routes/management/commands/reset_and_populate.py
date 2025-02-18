# apps/stations/management/commands/reset_and_populate.py
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
from apps.core.mixins import DatabaseConnectionMixin  # type: ignore


class Command(BaseCommand, DatabaseConnectionMixin):
    help = "Reset station IDs and repopulate routes"

    def add_arguments(self, parser):
        parser.add_argument(
            "--batch-size", type=int, default=50, help="Batch size for route population"
        )

    def handle(self, *args, **options):
        try:
            self.stdout.write("Starting reset and repopulate process...")

            with transaction.atomic():
                # Step 1: Clear and reset routes
                self.stdout.write("Clearing routes and resetting IDs...")
                call_command("populate_routes", "--clear")
                call_command("reset_station_ids")

                # Step 2: Repopulate routes
                self.stdout.write("Repopulating routes...")
                call_command("populate_routes", batch_size=options["batch_size"])

            self.stdout.write(
                self.style.SUCCESS("Successfully completed all operations")
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during process: {str(e)}"))
            raise
