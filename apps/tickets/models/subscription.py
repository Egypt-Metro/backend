# apps/tickets/models/subscription.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from ..constants.choices import SubscriptionChoices


class Subscription(models.Model):
    # Relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )

    # Subscription Details
    subscription_type = models.CharField(
        max_length=20,
        choices=SubscriptionChoices.TYPES,
        db_index=True
    )
    zones_count = models.PositiveIntegerField(
        choices=SubscriptionChoices.ZONES,
        validators=[MinValueValidator(1)],
        db_index=True
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    # Validity
    start_date = models.DateField(db_index=True)
    end_date = models.DateField(db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    # Zone Information
    covered_zones = models.JSONField(default=list)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_active'], name='user_active_idx'),
            models.Index(fields=['start_date', 'end_date'], name='validity_idx'),
            models.Index(fields=['subscription_type', 'zones_count'], name='type_zones_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(price__gte=0),
                name='subscription_price_non_negative'
            ),
            models.CheckConstraint(
                check=models.Q(end_date__gt=models.F('start_date')),
                name='end_date_after_start_date'
            ),
            models.CheckConstraint(
                check=(
                    models.Q(subscription_type='ANNUAL', zones_count__in=[2, 3])
                    | ~models.Q(subscription_type='ANNUAL')
                ),
                name='valid_annual_zones'
            )
        ]

    def __str__(self):
        return f"{self.get_subscription_type_display()} - {self.user.username}"

    def clean(self):
        super().clean()
        if self.end_date and self.start_date and self.end_date <= self.start_date:
            raise models.ValidationError("End date must be after start date")

        if self.start_date and self.start_date < timezone.now().date():
            raise models.ValidationError("Start date cannot be in the past")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
