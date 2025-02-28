from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),  # Replace with your last migration name
    ]

    operations = [
        # First drop the existing column
        migrations.RemoveField(
            model_name='user',
            name='subscription_type',
        ),
        # Then add it back with correct type
        migrations.AddField(
            model_name='user',
            name='subscription_type',
            field=models.CharField(
                max_length=10,
                choices=[
                    ('FREE', 'Free'),
                    ('BASIC', 'Basic'),
                    ('PREMIUM', 'Premium')
                ],
                default='FREE',
            ),
        ),
    ]
