# apps/users/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.core.exceptions import ValidationError
from .managers import CustomUserManager
from .constants.choices import SubscriptionType, PaymentMethod


class User(AbstractUser):
    """
    Extended User model with additional fields for Metro application.

    This model extends Django's AbstractUser to include:
    - National ID verification
    - Phone number validation
    - Subscription management
    - Payment handling
    - Balance tracking

    Note: Existing users will have default values for new fields.
    """

    # Basic user information
    email = models.EmailField(
        unique=True,
        error_messages={
            'unique': 'A user with this email already exists.',
        }
    )

    # Identity verification
    national_id = models.CharField(
        max_length=14,
        unique=True,
        null=True,
        blank=True,
        default=None,
        validators=[
            RegexValidator(
                r'^\d{14}$',
                'National ID must be exactly 14 digits.'
            )
        ],
        help_text='14-digit national identification number'
    )

    # Contact information
    phone_number = models.CharField(
        max_length=11,
        validators=[
            RegexValidator(
                r'^01[0-9]{9}$',
                'Phone number must start with 01 and be 11 digits long.'
            )
        ],
        unique=True,
        null=True,  # Allow null for existing users
        blank=True,  # Allow blank in forms
        help_text='Egyptian phone number format: 01XXXXXXXXX'
    )

    # Subscription and payment
    subscription_type = models.CharField(
        max_length=10,
        choices=SubscriptionType.choices,
        default=SubscriptionType.FREE.value,
        help_text='User subscription level'
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
        null=True,
        blank=True,
        help_text='Preferred payment method'
    )

    # Financial tracking
    balance = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text='Current account balance'
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,  # Automatically set when object is created
        help_text='Date and time when the user was created'
    )
    updated_at = models.DateTimeField(
        auto_now=True,  # Automatically updated on each save
        help_text='Date and time when the user was last updated'
    )

    # Custom manager for enhanced user operations
    objects = CustomUserManager()

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"

    def clean(self):
        """
        Custom validation for user data.
        Ensures all required fields are properly formatted.
        """
        super().clean()

        # Validate national ID format
        if self.national_id and not self.national_id.isdigit():
            raise ValidationError({
                'national_id': 'National ID must contain only digits.'
            })

        # Validate phone number format
        if self.phone_number and not self.phone_number.startswith('01'):
            raise ValidationError({
                'phone_number': 'Phone number must start with 01.'
            })

    def save(self, *args, **kwargs):
        """
        Override save method to ensure data consistency
        and perform any necessary calculations.
        """
        self.full_clean()  # Validate all fields

        # Ensure email is lowercase
        self.email = self.email.lower()

        # Update username if not set
        if not self.username:
            self.username = self.email.split('@')[0]

        super().save(*args, **kwargs)

    # Business logic methods
    def update_subscription(self, subscription_type):
        """Update user subscription and handle related changes"""
        self.subscription_type = subscription_type
        self.save()

    def add_balance(self, amount):
        """Add to user balance with validation"""
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        self.balance += amount
        self.save()

    def deduct_balance(self, amount):
        """Deduct from user balance with validation"""
        if amount < 0:
            raise ValueError("Amount cannot be negative")
        if self.balance < amount:
            raise ValueError("Insufficient balance")
        self.balance -= amount
        self.save()
