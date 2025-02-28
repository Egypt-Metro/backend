# apps/users/managers/user_manager.py
from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _
import time


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))

        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)

        # Generate default values for required fields
        timestamp = int(time.time() * 1000)

        # Don't set username here as it's already in extra_fields

        # Set default national_id if not provided
        if not extra_fields.get('national_id'):
            extra_fields['national_id'] = f"{timestamp:014d}"

        # Set default phone_number if not provided
        if not extra_fields.get('phone_number'):
            extra_fields['phone_number'] = f"01{str(timestamp)[-9:]}"

        # Set default subscription_type if not provided
        extra_fields.setdefault('subscription_type', 'FREE')

        user = self.model(email=email, **extra_fields)

        if password:
            user.set_password(password)

        try:
            user.save(using=self._db)
        except Exception as e:
            print(f"Error creating user: {str(e)}")
            raise

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('subscription_type', 'FREE')

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)

    def get_by_natural_key(self, email):
        return self.get(email=email)
