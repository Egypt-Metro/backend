# Generated by Django 4.2.18 on 2025-02-24 04:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0004_fix_subscription_type_production"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="subscription_type",
            field=models.CharField(
                choices=[("FREE", "Free"), ("BASIC", "Basic"), ("PREMIUM", "Premium")],
                default="FREE",
                help_text="User subscription level",
                max_length=10,
            ),
        ),
    ]
