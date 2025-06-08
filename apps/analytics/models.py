from django.db import models
from django.utils import timezone
from apps.stations.models import Station, Line
from apps.tickets.models import Ticket, UserSubscription


class StationAnalytics(models.Model):
    """Track analytics for each station"""
    station = models.OneToOneField(Station, on_delete=models.CASCADE, related_name='analytics')
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ticket_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subscription_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tickets_scanned = models.PositiveIntegerField(default=0)
    subscriptions_used = models.PositiveIntegerField(default=0)
    total_entries = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analytics for {self.station.name}"


class LineAnalytics(models.Model):
    """Track analytics for each metro line"""
    line = models.OneToOneField(Line, on_delete=models.CASCADE, related_name='analytics')
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ticket_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subscription_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tickets_scanned = models.PositiveIntegerField(default=0)
    subscriptions_used = models.PositiveIntegerField(default=0)
    total_entries = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analytics for Line {self.line.name}"


class TicketUsageRecord(models.Model):
    """Record each ticket usage for detailed analytics"""
    USAGE_TYPES = [
        ('ENTRY', 'Entry'),
        ('EXIT', 'Exit'),
    ]

    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='usage_records')
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='ticket_usages')
    line = models.ForeignKey(Line, on_delete=models.CASCADE, related_name='ticket_usages')
    timestamp = models.DateTimeField(default=timezone.now)
    revenue_amount = models.DecimalField(max_digits=10, decimal_places=2)
    usage_type = models.CharField(max_length=10, choices=USAGE_TYPES, default='ENTRY')

    def __str__(self):
        return f"Ticket {self.ticket.id} {self.usage_type.lower()} at {self.station.name} on {self.timestamp}"

    class Meta:
        # Ensure we don't record the same entry/exit event twice
        unique_together = ('ticket', 'station', 'usage_type')


class SubscriptionUsageRecord(models.Model):
    """Record each subscription usage for detailed analytics"""
    subscription = models.ForeignKey(UserSubscription, on_delete=models.CASCADE, related_name='usage_records')  # Changed from Subscription to UserSubscription
    station = models.ForeignKey(Station, on_delete=models.CASCADE, related_name='subscription_usages')
    line = models.ForeignKey(Line, on_delete=models.CASCADE, related_name='subscription_usages')
    timestamp = models.DateTimeField(default=timezone.now)
    revenue_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Subscription {self.subscription.id} used at {self.station.name} on {self.timestamp}"


class DailyAnalytics(models.Model):
    """Store daily analytics snapshots for trending and reporting"""
    date = models.DateField(unique=True)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    ticket_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subscription_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tickets_scanned = models.PositiveIntegerField(default=0)
    subscriptions_used = models.PositiveIntegerField(default=0)
    total_entries = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Daily Analytics"
        verbose_name_plural = "Daily Analytics"
        ordering = ['-date']

    def __str__(self):
        return f"Daily Analytics for {self.date}"
