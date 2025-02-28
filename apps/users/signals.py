# apps/users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to handle additional user setup after creation
    """
    if created:
        # You can add any additional setup needed when a user is created
        pass
