# apps/tickets/models/subscription.py
from django.db import models
from django.conf import settings
from django.utils import timezone


class SubscriptionPlan(models.Model):
    """Model representing available subscription plans"""
    SUBSCRIPTION_TYPE_CHOICES = [
        ('MONTHLY', 'Monthly Subscription'),
        ('QUARTERLY', 'Quarterly Subscription'),
        ('ANNUAL', 'Annual Subscription'),
    ]

    name = models.CharField(max_length=100)
    type = models.CharField(max_length=10, choices=SUBSCRIPTION_TYPE_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    zones = models.PositiveIntegerField(null=True, blank=True, help_text="Zones covered (for Monthly/Quarterly)")
    lines = models.JSONField(null=True, blank=True, help_text="Lines covered (for Annual)")
    description = models.TextField(blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['type']),
        ]

    def __str__(self):
        if self.type == 'ANNUAL':
            return f"{self.name} - {self.lines} - {self.price} EGP"
        return f"{self.name} - {self.zones} zones - {self.price} EGP"


class UserSubscription(models.Model):
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='ACTIVE')

    # Optional fields for user's regular journey
    start_station = models.ForeignKey(
        'stations.Station',
        on_delete=models.SET_NULL,
        null=True,
        related_name='subscription_starts'
    )
    end_station = models.ForeignKey(
        'stations.Station',
        on_delete=models.SET_NULL,
        null=True,
        related_name='subscription_ends'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"

    @property
    def is_active(self):
        return (
            self.status == 'ACTIVE' and self.start_date <= timezone.now().date() <= self.end_date
        )

    def save(self, *args, **kwargs):
        if not self.pk:  # Only on creation
            if self.start_date is None:
                self.start_date = timezone.now().date()

            # Set end_date based on subscription type
            if self.plan.type == 'MONTHLY':
                self.end_date = self.start_date + timezone.timedelta(days=30)
            elif self.plan.type == 'QUARTERLY':
                self.end_date = self.start_date + timezone.timedelta(days=90)
            else:  # ANNUAL
                self.end_date = self.start_date + timezone.timedelta(days=365)

        super().save(*args, **kwargs)


class StationZone(models.Model):
    """Maps stations to their zones"""
    station = models.ForeignKey('stations.Station', on_delete=models.CASCADE, related_name='zone')
    zone_number = models.PositiveIntegerField()

    class Meta:
        unique_together = ('station', 'zone_number')

    def __str__(self):
        return f"{self.station.name} - Zone {self.zone_number}"


class ZoneMatrix(models.Model):
    """Stores the number of zones between any two zones"""
    source_zone = models.PositiveIntegerField()
    destination_zone = models.PositiveIntegerField()
    zones_crossed = models.PositiveIntegerField()

    class Meta:
        unique_together = ('source_zone', 'destination_zone')
        indexes = [
            models.Index(fields=['source_zone', 'destination_zone']),
        ]

    def __str__(self):
        return f"Zone {self.source_zone} to Zone {self.destination_zone}: {self.zones_crossed} zones"
