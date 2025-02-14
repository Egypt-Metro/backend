# apps/stations/management/commands/setup_static.py
import shutil
from pathlib import Path
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Sets up static files including metro map'

    def handle(self, *args, **options):
        static_dir = Path('static/images')
        static_dir.mkdir(parents=True, exist_ok=True)

        # Copy metro map
        shutil.copy(
            'docs/metro-map.png',
            static_dir / 'metro-map.png'
        )

        self.stdout.write(self.style.SUCCESS('Static files setup completed'))
