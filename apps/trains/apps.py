# apps/trains/apps.py

from django.apps import AppConfig


class TrainsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.trains'
    verbose_name = 'Trains'

    def ready(self):
        try:
            import apps.trains.signals  # noqa: F401
        except ImportError:
            pass
