from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.analytics'

    def ready(self):
        # No need to import signals here - they should be imported in the ticket app's ready method
        pass
