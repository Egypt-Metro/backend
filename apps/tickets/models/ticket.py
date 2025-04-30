# apps/tickets/models/ticket.py
import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from ..constants.choices import TicketChoices


def generate_ticket_number():
    """Generate a unique ticket number"""
    return f"TKT-{uuid.uuid4().hex[:8].upper()}"


class Ticket(models.Model):
    # Identifiers
    ticket_number = models.CharField(
        max_length=50,
        unique=True,
        default=generate_ticket_number,
        editable=False
    )
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        db_index=True
    )

    # Relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tickets'
    )

    # Ticket Details
    ticket_type = models.CharField(
        max_length=20,
        choices=TicketChoices.get_ticket_type_choices(),
        default='BASIC',
        db_index=True,
        help_text="Type of ticket",
        verbose_name="Ticket Type"
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        help_text="Price of the ticket",
        verbose_name="Ticket Price"
    )
    status = models.CharField(
        max_length=15,
        choices=TicketChoices.STATUS,
        default='ACTIVE',
        db_index=True
    )
    color = models.CharField(
        max_length=10,
        choices=TicketChoices.TICKET_COLORS,
        db_index=True
    )
    max_stations = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text="Maximum number of stations allowed for this ticket"
    )

    # Upgrade status
    needs_upgrade = models.BooleanField(default=False, help_text="Flag indicating this ticket needs upgrading")
    temp_exit_station = models.ForeignKey(
        'stations.Station',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='temp_ticket_exits'
    )

    # Station Information
    entry_station = models.ForeignKey(
        'stations.Station',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='ticket_entries'
    )
    exit_station = models.ForeignKey(
        'stations.Station',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='ticket_exits'
    )

    # Timing Information
    entry_time = models.DateTimeField(null=True, blank=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField()

    # QR Code and Validation
    qr_code = models.TextField(blank=True)
    validation_hash = models.CharField(max_length=255, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ticket_number'], name='ticket_number_idx'),
            models.Index(fields=['status'], name='ticket_status_idx'),
            models.Index(fields=['user', 'status'], name='user_status_idx'),
            models.Index(fields=['entry_station', 'exit_station'], name='stations_idx'),
            models.Index(fields=['valid_until'], name='valid_until_idx'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(price__gte=0),
                name='ticket_price_non_negative'
            )
        ]

    def __str__(self):
        return f"Ticket {self.ticket_number} - {self.status}"

    def clean(self):
        super().clean()
        if self.exit_time and self.entry_time and self.exit_time < self.entry_time:
            raise models.ValidationError("Exit time cannot be before entry time")

        if self.valid_until and self.valid_until < timezone.now():
            raise models.ValidationError("Valid until date must be in the future")

    def save(self, *args, **kwargs):
        if not self.pk:  # New ticket
            # Set default values from ticket type
            ticket_config = TicketChoices.TICKET_TYPES.get(self.ticket_type)
            if ticket_config:
                self.price = ticket_config['price']
                self.color = ticket_config['color']
                self.max_stations = ticket_config['max_stations']

        self.full_clean()
        super().save(*args, **kwargs)
