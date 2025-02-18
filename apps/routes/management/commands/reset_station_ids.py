from django.core.management.base import BaseCommand
from django.db import connection, transaction
from apps.stations.models import Station, LineStation, ConnectingStation
from apps.routes.models import Route
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Reset station IDs to start from 1'

    def handle(self, *args, **options):
        try:
            with transaction.atomic():
                self.stdout.write('Starting ID reset process...')

                # Backup current data
                self.backup_current_state()

                # Create and validate ID mapping
                id_mapping = self.create_id_mapping()

                # Update references using temporary IDs
                self.update_references(id_mapping)

                # Finalize ID updates
                self.finalize_updates(id_mapping)

                # Reset database sequence
                self.reset_sequence()

                # Verify data integrity
                self.verify_data_integrity(id_mapping)

                self.stdout.write(self.style.SUCCESS(
                    f'Successfully reset IDs for {len(id_mapping)} stations'
                ))

        except Exception as e:
            logger.error(f"Failed to reset station IDs: {str(e)}")
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            raise

    def backup_current_state(self):
        """Create a backup of current state"""
        self.stdout.write('Creating backup of current state...')
        self.original_stations = list(Station.objects.all().values())
        self.original_line_stations = list(LineStation.objects.all().values())
        self.original_connecting_stations = list(ConnectingStation.objects.all().values())
        self.original_routes = list(Route.objects.all().values())

    def create_id_mapping(self):
        """Create mapping between old and new IDs"""
        self.stdout.write('Creating ID mapping...')
        id_mapping = {}
        stations = Station.objects.all().order_by('name')

        for new_id, station in enumerate(stations, 1):
            id_mapping[station.id] = new_id

        return id_mapping

    def update_references(self, id_mapping):
        """Update all references using temporary IDs"""
        self.stdout.write('Updating references...')

        # Use temporary IDs (offset by 10000 to avoid conflicts)
        for old_id, new_id in id_mapping.items():
            temp_id = new_id + 10000

            # Update LineStation references
            LineStation.objects.filter(station_id=old_id).update(
                station_id=temp_id
            )

            # Update ConnectingStation references
            ConnectingStation.objects.filter(station_id=old_id).update(
                station_id=temp_id
            )

            # Update Route references
            Route.objects.filter(start_station_id=old_id).update(
                start_station_id=temp_id
            )
            Route.objects.filter(end_station_id=old_id).update(
                end_station_id=temp_id
            )

            # Update Station IDs
            Station.objects.filter(id=old_id).update(
                id=temp_id
            )

    def finalize_updates(self, id_mapping):
        """Finalize ID updates by removing temporary offset"""
        self.stdout.write('Finalizing ID updates...')

        for old_id, new_id in id_mapping.items():
            temp_id = new_id + 10000

            # Update all references from temporary to final IDs
            Station.objects.filter(id=temp_id).update(id=new_id)
            LineStation.objects.filter(station_id=temp_id).update(station_id=new_id)
            ConnectingStation.objects.filter(station_id=temp_id).update(station_id=new_id)
            Route.objects.filter(start_station_id=temp_id).update(start_station_id=new_id)
            Route.objects.filter(end_station_id=temp_id).update(end_station_id=new_id)

    def reset_sequence(self):
        """Reset database sequence"""
        self.stdout.write('Resetting database sequence...')
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT setval(pg_get_serial_sequence('stations_station', 'id'),
                           (SELECT COALESCE(MAX(id), 1) FROM stations_station));
            """)

    def verify_data_integrity(self, id_mapping):
        """Verify data integrity after updates"""
        self.stdout.write('Verifying data integrity...')

        valid_ids = set(id_mapping.values())

        # Verify Station IDs
        invalid_stations = Station.objects.exclude(id__in=valid_ids)
        if invalid_stations.exists():
            raise ValueError(f"Found {invalid_stations.count()} invalid station IDs")

        # Verify LineStation references
        invalid_ls = LineStation.objects.exclude(station_id__in=valid_ids)
        if invalid_ls.exists():
            raise ValueError(f"Found {invalid_ls.count()} invalid LineStation references")

        # Verify ConnectingStation references
        invalid_cs = ConnectingStation.objects.exclude(station_id__in=valid_ids)
        if invalid_cs.exists():
            raise ValueError(f"Found {invalid_cs.count()} invalid ConnectingStation references")

        # Verify Route references
        invalid_routes = Route.objects.exclude(
            start_station_id__in=valid_ids,
            end_station_id__in=valid_ids
        )
        if invalid_routes.exists():
            raise ValueError(f"Found {invalid_routes.count()} invalid Route references")

    def rollback_changes(self):
        """Rollback changes in case of failure"""
        self.stdout.write('Rolling back changes...')
        try:
            with transaction.atomic():
                # Restore original data
                Station.objects.all().delete()
                LineStation.objects.all().delete()
                ConnectingStation.objects.all().delete()
                Route.objects.all().delete()

                Station.objects.bulk_create([Station(**data) for data in self.original_stations])
                LineStation.objects.bulk_create([LineStation(**data) for data in self.original_line_stations])
                ConnectingStation.objects.bulk_create([ConnectingStation(**data) for data in self.original_connecting_stations])
                Route.objects.bulk_create([Route(**data) for data in self.original_routes])

                self.stdout.write(self.style.SUCCESS('Successfully rolled back changes'))
        except Exception as e:
            logger.error(f"Failed to rollback changes: {str(e)}")
            raise
