# Generated by Django 5.1.3 on 2024-12-05 03:42

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_alter_user_username'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='phone_number',
            field=models.CharField(blank=True, max_length=11, null=True, validators=[django.core.validators.RegexValidator('^01\\d{9}$', "Phone number must start with '01', followed by exactly 9 digits.")]),
        ),
    ]