# apps/routes/management/commands/verify_stations.py

from django.core.management.base import BaseCommand
from apps.stations.models import Station, LineStation


class Command(BaseCommand):
    help = 'Verify and fix station data'

    def handle(self, *args, **options):
        try:
            # Get all stations and their lines
            stations = Station.objects.prefetch_related('lines').all()

            self.stdout.write(f"Found {stations.count()} stations")

            # Check each station
            issues = []
            for station in stations:
                # Check if station has lines
                if not station.lines.exists():
                    issues.append(f"Station {station.name} has no lines")
                    continue

                # Check line stations
                for line in station.lines.all():
                    try:
                        line_station = LineStation.objects.get(
                            station=station,
                            line=line
                        )
                        if line_station.order is None:
                            issues.append(f"Station {station.name} has no order on {line.name}")
                    except LineStation.DoesNotExist:
                        issues.append(f"Missing LineStation for {station.name} on {line.name}")

            if issues:
                self.stdout.write("\nFound issues:")
                for issue in issues:
                    self.stdout.write(f"- {issue}")
            else:
                self.stdout.write(self.style.SUCCESS("All stations verified successfully"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))
