from django.apps import AppConfig


class TicketsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tickets'
    verbose_name = 'Tickets Management'
    label = 'tickets'
    path = 'apps/tickets'
    icon = 'mdi:ticket-confirmation'

    def ready(self):
        # Explicitly import the signals module
        from apps.tickets import signals  # noqa
        print("Ticket signals registered successfully!")
