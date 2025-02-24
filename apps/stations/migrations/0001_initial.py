# Generated by Django 5.1.3 on 2024-12-11 19:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Line",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255, unique=True)),
                (
                    "color_code",
                    models.CharField(
                        blank=True,
                        help_text="Format: #RRGGBB",
                        max_length=10,
                        null=True,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="LineStation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("order", models.PositiveIntegerField()),
                (
                    "line",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="line_stations",
                        to="stations.line",
                    ),
                ),
            ],
            options={
                "ordering": ["order"],
            },
        ),
        migrations.CreateModel(
            name="Station",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=255, unique=True)),
                ("latitude", models.FloatField(blank=True, null=True)),
                ("longitude", models.FloatField(blank=True, null=True)),
                (
                    "lines",
                    models.ManyToManyField(
                        related_name="stations",
                        through="stations.LineStation",
                        to="stations.line",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="linestation",
            name="station",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="station_lines",
                to="stations.station",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="linestation",
            unique_together={("line", "station")},
        ),
    ]
