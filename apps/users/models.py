from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator


# Create your models here.
class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True, null=False, blank=False)
    email = models.EmailField(unique=True, null=False, blank=False)
    national_id = models.CharField(
        max_length=14,
        unique=True,
        validators=[
            RegexValidator(r"^\d{14}$", "National ID must be exactly 14 digits.")
        ],
    )
    phone_number = models.CharField(
        max_length=11,  # Ensures max length of 11
        validators=[
            RegexValidator(
                r"^01\d{9}$",  # Starts with '01' and followed by exactly 9 digits
                "Phone number must start with '01' followed by 9 digits.",
            )
        ],
        blank=True,
        null=True,
    )
    subscription_type = models.BooleanField(default=False)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optionally add meta information for better management
    class Meta:
        db_table = "users"  # Ensure it matches the SQL table name
        verbose_name = db_table[
            :-1
        ].capitalize()  # Generate singular name ('users' -> 'User')
        verbose_name_plural = (
            db_table.capitalize()
        )  # Capitalize the table name ('users' -> 'Users')

    # Define __str__ for better object representation
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
