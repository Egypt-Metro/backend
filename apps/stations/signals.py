# apps/stations/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import LineStation
from apps.routes.services.cache_service import CacheService


@receiver(post_save, sender=LineStation)
@receiver(post_delete, sender=LineStation)
def clear_route_cache(sender, instance, **kwargs):
    """ Clears only routes related to the affected LineStation """

    # Prevent signal execution during migrations
    if kwargs.get("raw", False):
        return

    # Get start and end station from instance
    start_station = instance.start_station
    end_station = instance.end_station

    # Clear only affected routes in cache
    CacheService.clear_routes_for_stations(start_station, end_station)
