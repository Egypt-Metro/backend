from django.utils import timezone
import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _


class Transaction(models.Model):
    """Record of all financial transactions in the system"""
    TRANSACTION_TYPES = [
        ('DEPOSIT', _('Deposit')),
        ('WITHDRAW', _('Withdrawal')),
        ('PAYMENT', _('Payment')),
        ('REFUND', _('Refund')),
        ('TICKET_PURCHASE', _('Ticket Purchase')),
        ('SUBSCRIPTION_PURCHASE', _('Subscription Purchase')),
        ('TICKET_UPGRADE', _('Ticket Upgrade')),
    ]

    TRANSACTION_STATUS = [
        ('PENDING', _('Pending')),
        ('COMPLETED', _('Completed')),
        ('FAILED', _('Failed')),
        ('CANCELLED', _('Cancelled')),
        ('REFUNDED', _('Refunded')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    wallet = models.ForeignKey(
        'wallet.UserWallet',
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )
    type = models.CharField(max_length=30, choices=TRANSACTION_TYPES)
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='PENDING')

    # For linking to purchased items
    related_object_type = models.CharField(max_length=50, blank=True, null=True)
    related_object_id = models.CharField(max_length=50, blank=True, null=True)

    payment_method = models.ForeignKey(
        'wallet.PaymentMethod',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )

    reference_number = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("Transaction")
        verbose_name_plural = _("Transactions")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user'], name='transaction_user_idx'),
            models.Index(fields=['wallet'], name='transaction_wallet_idx'),
            models.Index(fields=['type'], name='transaction_type_idx'),
            models.Index(fields=['status'], name='transaction_status_idx'),
            models.Index(fields=['created_at'], name='transaction_date_idx'),
            models.Index(fields=['related_object_type', 'related_object_id'],
                         name='transaction_related_idx'),
        ]

    def __str__(self):
        return f"{self.get_type_display()} - {self.amount} EGP - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # Set completed_at when transaction is completed
        if self.status == 'COMPLETED' and not self.completed_at:
            self.completed_at = timezone.now()
        super().save(*args, **kwargs)
