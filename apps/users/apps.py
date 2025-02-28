# apps/users/apps.py
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _  # Updated import


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = _('Users')

    def ready(self):
        """
        Import signals and perform any other initialization
        """
        try:
            import apps.users.signals  # noqa
        except ImportError:
            pass
