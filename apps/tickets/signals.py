import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.tickets.models import Ticket, UserSubscription
from apps.analytics.services import record_ticket_usage, record_subscription_usage

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Ticket)
def track_ticket_usage(sender, instance, created, **kwargs):
    """Track ticket usage for both entry and exit events"""
    if created:
        return  # Skip new ticket creation

    try:
        # Track entry (ACTIVE → IN_USE)
        if instance.status == 'IN_USE' and instance.entry_station:
            logger.info(f"Tracking entry for ticket {instance.ticket_number} at station {instance.entry_station.name}")
            record_ticket_usage(
                ticket_id=instance.id,
                station_id=instance.entry_station.id,
                usage_type='ENTRY'
            )

        # Track exit (IN_USE → USED) - could use different analytics if needed
        elif instance.status == 'USED' and instance.exit_station:
            logger.info(f"Tracking exit for ticket {instance.ticket_number} at station {instance.exit_station.name}")
            # Optionally record exit analytics (could be a separate function if needed)
            # For now, we'll continue to attribute revenue to the entry station

    except Exception as e:
        logger.error(f"Error recording ticket analytics: {str(e)}", exc_info=True)
        print(f"Error recording ticket analytics: {str(e)}")


@receiver(post_save, sender=UserSubscription)
def track_subscription_usage(sender, instance, created, **kwargs):
    """Track subscription activation and usage"""
    if created:
        return  # Skip new subscription creation

    try:
        # Track when subscription becomes active
        if instance.status == 'ACTIVE' and instance.start_station:
            logger.info(f"Tracking activation for subscription {instance.id} at station {instance.start_station.name}")
            record_subscription_usage(instance.id, instance.start_station.id)

    except Exception as e:
        logger.error(f"Error recording subscription analytics: {str(e)}", exc_info=True)
        print(f"Error recording subscription analytics: {str(e)}")
