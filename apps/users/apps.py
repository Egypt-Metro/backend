from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = _('Users')

    def ready(self):
        from django.contrib import admin
        # Ensure admin customizations are loaded
        admin.site.site_header = "Egypt Metro Administration"
        admin.site.site_title = "Egypt Metro Admin Portal"
        admin.site.index_title = "Welcome to Egypt Metro Admin Portal"
