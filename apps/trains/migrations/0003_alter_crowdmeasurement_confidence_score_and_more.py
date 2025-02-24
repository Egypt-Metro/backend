# Generated by Django 4.2.18 on 2025-02-23 00:26

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("trains", "0002_alter_train_train_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="crowdmeasurement",
            name="confidence_score",
            field=models.DecimalField(
                decimal_places=2,
                help_text="Confidence level of the measurement (0-1)",
                max_digits=3,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(1),
                ],
            ),
        ),
        migrations.AlterField(
            model_name="crowdmeasurement",
            name="crowd_percentage",
            field=models.DecimalField(
                decimal_places=2,
                max_digits=5,
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(100),
                ],
            ),
        ),
    ]
