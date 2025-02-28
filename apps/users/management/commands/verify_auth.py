# apps/users/management/commands/verify_auth.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model, authenticate
from django.conf import settings


class Command(BaseCommand):
    help = 'Verify authentication settings and user credentials'

    def handle(self, *args, **options):
        User = get_user_model()

        self.stdout.write("\n=== Authentication Verification ===")

        # Print environment info
        self.stdout.write(f"\nEnvironment: {settings.ENVIRONMENT}")
        self.stdout.write(f"Debug: {settings.DEBUG}")
        self.stdout.write(f"Database: {settings.DATABASES['default']['NAME']}")

        # List all superusers
        superusers = User.objects.filter(is_superuser=True)
        self.stdout.write("\nSuperusers:")
        for user in superusers:
            self.stdout.write(
                f"- {user.username} (Email: {user.email}, Active: {user.is_active})"
            )

        # Test authentication
        username = input("\nEnter username to test: ")
        password = input("Enter password: ")

        user = authenticate(username=username, password=password)

        if user:
            self.stdout.write(
                self.style.SUCCESS(
                    f"\nAuthentication successful:"
                    f"\nUsername: {user.username}"
                    f"\nEmail: {user.email}"
                    f"\nIs active: {user.is_active}"
                    f"\nIs staff: {user.is_staff}"
                    f"\nIs superuser: {user.is_superuser}"
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR("\nAuthentication failed!")
            )
