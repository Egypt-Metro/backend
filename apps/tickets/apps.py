from django.apps import AppConfig


class TicketsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tickets'
    verbose_name = 'Tickets Management'
    label = 'tickets'
    path = 'apps/tickets'
    icon = 'mdi:ticket-confirmation'
