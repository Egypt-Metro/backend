from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0006_alter_user_national_id'),  # Replace with actual previous migration
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='national_id',
            field=models.CharField(
                max_length=14,
                unique=True,
                null=True,
                blank=True,
                help_text='14-digit national identification number'
            ),
        ),
        migrations.AlterField(
            model_name='user',
            name='phone_number',
            field=models.CharField(
                max_length=11,
                unique=True,
                null=True,
                blank=True,
                help_text='Egyptian phone number format: 01XXXXXXXXX'
            ),
        ),
    ]
