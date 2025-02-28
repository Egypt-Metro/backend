# apps/users/migrations/0004_fix_subscription_type_production.py
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_user_subscription_type'),  # Replace with your last migration
    ]

    operations = [
        # First, add a temporary column
        migrations.AddField(
            model_name='user',
            name='subscription_type_new',
            field=models.CharField(
                max_length=10,
                null=True,
                choices=[
                    ('FREE', 'Free'),
                    ('BASIC', 'Basic'),
                    ('PREMIUM', 'Premium')
                ],
            ),
        ),
        
        # Convert data using Python
        migrations.RunPython(
            code=lambda apps, schema_editor: apps.get_model('users', 'User').objects.update(
                subscription_type_new='FREE'
            ),
            reverse_code=migrations.RunPython.noop
        ),
        
        # Remove old column
        migrations.RemoveField(
            model_name='user',
            name='subscription_type',
        ),
        
        # Rename new column
        migrations.RenameField(
            model_name='user',
            old_name='subscription_type_new',
            new_name='subscription_type',
        ),
        
        # Make it non-nullable with default
        migrations.AlterField(
            model_name='user',
            name='subscription_type',
            field=models.CharField(
                max_length=10,
                default='FREE',
                choices=[
                    ('FREE', 'Free'),
                    ('BASIC', 'Basic'),
                    ('PREMIUM', 'Premium')
                ],
            ),
        ),
    ]