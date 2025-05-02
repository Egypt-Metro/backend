import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _


class UserWallet(models.Model):
    """User's digital wallet for storing funds and making payments"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        help_text=_("Current wallet balance")
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("User Wallet")
        verbose_name_plural = _("User Wallets")
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['user'], name='wallet_user_idx'),
            models.Index(fields=['is_active'], name='wallet_active_idx'),
        ]

    def __str__(self):
        return f"{self.user.username}'s Wallet (Balance: {self.balance} EGP)"

    def add_funds(self, amount):
        """Add funds to the wallet"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        self.balance += amount
        self.save(update_fields=['balance', 'updated_at'])
        return self.balance

    def withdraw_funds(self, amount):
        """Withdraw funds from the wallet"""
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self.balance -= amount
        self.save(update_fields=['balance', 'updated_at'])
        return self.balance
