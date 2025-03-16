# apps/dashboard/singals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import SystemAlert


@receiver(post_save, sender=SystemAlert)
def handle_system_alert(sender, instance, created, **kwargs):
    """
    Handle system alert creation and resolution
    """
    if created:
        # Perform actions on alert creation
        # e.g., send notifications, log events
        pass

    if instance.is_resolved and not instance.resolved_at:
        instance.resolved_at = timezone.now()
        instance.save()
