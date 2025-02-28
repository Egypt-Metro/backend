# apps/users/management/commands/reset_admin.py

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Reset admin credentials'

    def handle(self, *args, **kwargs):
        try:
            with transaction.atomic():
                # Create or update admin user
                admin_user = User.objects.update_or_create(
                    email='admin@example.com',
                    defaults={
                        'username': 'admin',
                        'is_staff': True,
                        'is_superuser': True,
                        'is_active': True,
                        'subscription_type': 'FREE',
                    }
                )[0]
                admin_user.set_password('123')
                admin_user.save()

                # Create or update metro user
                metro_user = User.objects.update_or_create(
                    email='metro@gmail.com',
                    defaults={
                        'username': 'metro',
                        'is_staff': True,
                        'is_superuser': True,
                        'is_active': True,
                        'subscription_type': 'FREE',
                    }
                )[0]
                metro_user.set_password('123')
                metro_user.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        '\nAdmin credentials reset successfully!\n\n'
                        'Admin User:\n'
                        '  Email: admin@example.com\n'
                        '  Password: 123\n\n'
                        'Metro User:\n'
                        '  Email: metro@gmail.com\n'
                        '  Password: 123\n'
                    )
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error resetting admin credentials: {str(e)}')
            )
