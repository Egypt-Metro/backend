# apps/users/management/commands/verify_and_fix_users.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.users.constants.choices import SubscriptionType
from apps.users.models import User
from apps.users.services.data_integrity_service import UserDataIntegrityService


class Command(BaseCommand):
    help = 'Verify and fix user data comprehensively'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix issues automatically',
        )
        parser.add_argument(
            '--backup',
            action='store_true',
            help='Create backup before making changes',
        )

    def handle(self, *args, **options):
        # Changed HEADING to SUCCESS for the initial message
        self.stdout.write(
            self.style.SUCCESS("=== Starting user data verification ===")
        )
        
        if options['backup']:
            self._create_backup()

        service = UserDataIntegrityService()
        users = User.objects.all()
        issues_found = False
        fixed_count = 0

        for user in users:
            issues = self._verify_user(user)
            
            if issues:
                issues_found = True
                self.stdout.write(
                    self.style.WARNING(
                        f"\nUser {user.username} (ID: {user.id}) has issues:"
                    )
                )
                for issue in issues:
                    self.stdout.write(f"  - {issue}")
                
                if options['fix']:
                    fixed = self._fix_user(user)
                    if fixed:
                        fixed_count += 1

        # Generate and display report
        report = service.generate_report()
        self.stdout.write(
            self.style.SUCCESS("\n=== User Data Report ===")
        )
        for key, value in report.items():
            self.stdout.write(f"{key}: {value}")

        # Summary
        if issues_found:
            if options['fix']:
                self.stdout.write(
                    self.style.SUCCESS(f"\nFixed {fixed_count} users with issues")
                )
            else:
                self.stdout.write(
                    self.style.WARNING("\nRun with --fix to attempt automatic fixes")
                )
        else:
            self.stdout.write(
                self.style.SUCCESS("\nNo issues found - All data is valid")
            )

    def _verify_user(self, user):
        """Verify all required user data"""
        issues = []
        
        # Check required fields
        if not user.email:
            issues.append("Missing email")
        if not user.username:
            issues.append("Missing username")
        
        # Check custom fields
        if not user.national_id:
            issues.append("Missing national_id")
        if not user.subscription_type:
            issues.append("Missing subscription_type")
        if user.balance is None:
            issues.append("Missing balance")
        if user.created_at is None:
            issues.append("Missing created_at timestamp")
        if user.updated_at is None:
            issues.append("Missing updated_at timestamp")
            
        # Validate phone number format
        if user.phone_number and not user.phone_number.startswith('01'):
            issues.append("Invalid phone number format")
            
        return issues

    def _fix_user(self, user):
        """Attempt to fix user data issues"""
        try:
            # Set default values for missing fields
            if not user.national_id:
                user.national_id = f"DEFAULT{user.id:010d}"
            if not user.subscription_type:
                user.subscription_type = SubscriptionType.FREE
            if user.balance is None:
                user.balance = 0.00
            if user.created_at is None:
                user.created_at = user.date_joined or timezone.now()
            if user.updated_at is None:
                user.updated_at = timezone.now()
                
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f"  ✓ Fixed issues for user {user.username}")
            )
            return True
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  ✗ Failed to fix user {user.username}: {str(e)}")
            )
            return False

    def _create_backup(self):
        """Create a backup of user data"""
        from django.core import serializers
        import json
        from datetime import datetime
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'user_backup_{timestamp}.json'
        
        self.stdout.write(
            self.style.SUCCESS("\n=== Creating backup ===")
        )
        
        users = User.objects.all()
        data = serializers.serialize('json', users)
        
        with open(filename, 'w') as f:
            json.dump(json.loads(data), f, indent=2)
            
        self.stdout.write(
            self.style.SUCCESS(f"✓ Backup created: {filename}")
        )