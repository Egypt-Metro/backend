import uuid
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class PaymentMethod(models.Model):
    """Payment methods that users can use to add funds to their wallet"""
    PAYMENT_TYPES = [
        ('CREDIT_CARD', _('Credit Card')),
        ('DEBIT_CARD', _('Debit Card')),
        ('BANK_TRANSFER', _('Bank Transfer')),
        ('MOBILE_WALLET', _('Mobile Wallet')),
        ('CASH', _('Cash')),
        ('OTHER', _('Other')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payment_methods'
    )
    payment_type = models.CharField(max_length=30, choices=PAYMENT_TYPES)

    # For storing sensitive data in a secure way
    details = models.JSONField(default=dict, blank=True)

    # For cards
    card_last4 = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=20, blank=True)
    card_expiry_month = models.PositiveSmallIntegerField(null=True, blank=True)
    card_expiry_year = models.PositiveSmallIntegerField(null=True, blank=True)

    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    name = models.CharField(max_length=100, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Payment Method")
        verbose_name_plural = _("Payment Methods")
        ordering = ['-is_default', '-created_at']
        indexes = [
            models.Index(fields=['user'], name='payment_method_user_idx'),
            models.Index(fields=['payment_type'], name='payment_method_type_idx'),
            models.Index(fields=['is_default'], name='payment_method_default_idx'),
            models.Index(fields=['is_active'], name='payment_method_active_idx'),
        ]

    def __str__(self):
        if self.name:
            return f"{self.name} ({self.get_payment_type_display()})"
        return f"{self.get_payment_type_display()} ending in {self.card_last4 or 'N/A'}"

    def save(self, *args, **kwargs):
        # If this is being set as default, unset any existing default
        if self.is_default:
            PaymentMethod.objects.filter(
                user=self.user,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
