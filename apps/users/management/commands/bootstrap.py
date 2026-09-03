# apps/users/management/commands/bootstrap.py
"""
Idempotent first-run setup for a fresh deployment.

Runs on every container start (see render.yaml startCommand) but only *acts*
when something is missing, so it is safe to run repeatedly:

- creates the default admin accounts only if no superuser exists yet
- seeds metro data (lines / stations / routes / trains) only if there are no
  stations yet

This lets a host with no shell access (e.g. Render's free tier) come up fully
populated on the first deploy.
"""

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Idempotent first-run setup: default admin + seed data if the DB is empty."

    def handle(self, *args, **options):
        User = get_user_model()

        if not User.objects.filter(is_superuser=True).exists():
            self.stdout.write("No superuser found -> creating default admin accounts")
            call_command("reset_admin")
            self.stdout.write(self.style.WARNING(
                "Default admin created (admin@example.com / 123). "
                "Change this password immediately in /admin/."
            ))
        else:
            self.stdout.write("Superuser already exists -> skipping admin creation")

        try:
            from apps.stations.models import Station
        except Exception as exc:  # pragma: no cover - app layout guard
            self.stderr.write(f"Could not import Station model: {exc}")
            return

        if Station.objects.exists():
            self.stdout.write("Stations already present -> skipping seed")
            return

        self.stdout.write("Empty database -> seeding metro data")
        for command in ("populate_metro_data", "populate_routes", "generate_test_data"):
            try:
                call_command(command)
                self.stdout.write(self.style.SUCCESS(f"  {command} OK"))
            except Exception as exc:
                self.stderr.write(f"  {command} skipped: {exc}")
