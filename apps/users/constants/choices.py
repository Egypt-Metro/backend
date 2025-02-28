# apps/users/constants/choices.py
from django.db import models


class SubscriptionType(models.TextChoices):
    FREE = 'FREE', 'Free'
    BASIC = 'BASIC', 'Basic'
    PREMIUM = 'PREMIUM', 'Premium'


class PaymentMethod(models.TextChoices):
    CREDIT_CARD = 'CREDIT_CARD', 'Credit Card'
    WALLET = 'WALLET', 'Digital Wallet'


# constants/messages.py
class UserMessages:
    REGISTRATION_SUCCESS = "User registered successfully"
    LOGIN_SUCCESS = "Login successful"
    INVALID_CREDENTIALS = "Invalid credentials"
    PROFILE_UPDATED = "Profile updated successfully"
