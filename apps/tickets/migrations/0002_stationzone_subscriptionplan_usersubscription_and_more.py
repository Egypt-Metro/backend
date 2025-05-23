# Generated by Django 4.2.18 on 2025-04-23 19:23

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("stations", "0005_connectingstation"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("tickets", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="StationZone",
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
                ("zone_number", models.PositiveIntegerField()),
            ],
        ),
        migrations.CreateModel(
            name="SubscriptionPlan",
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
                ("name", models.CharField(max_length=100)),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("MONTHLY", "Monthly Subscription"),
                            ("QUARTERLY", "Quarterly Subscription"),
                            ("ANNUAL", "Annual Subscription"),
                        ],
                        max_length=10,
                    ),
                ),
                ("price", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "zones",
                    models.PositiveIntegerField(
                        blank=True,
                        help_text="Zones covered (for Monthly/Quarterly)",
                        null=True,
                    ),
                ),
                (
                    "lines",
                    models.JSONField(
                        blank=True, help_text="Lines covered (for Annual)", null=True
                    ),
                ),
                ("description", models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="UserSubscription",
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
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("ACTIVE", "Active"),
                            ("EXPIRED", "Expired"),
                            ("CANCELLED", "Cancelled"),
                        ],
                        default="ACTIVE",
                        max_length=10,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ZoneMatrix",
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
                ("source_zone", models.PositiveIntegerField()),
                ("destination_zone", models.PositiveIntegerField()),
                ("zones_crossed", models.PositiveIntegerField()),
            ],
        ),
        migrations.DeleteModel(
            name="Subscription",
        ),
        migrations.AddIndex(
            model_name="zonematrix",
            index=models.Index(
                fields=["source_zone", "destination_zone"],
                name="tickets_zon_source__52a246_idx",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="zonematrix",
            unique_together={("source_zone", "destination_zone")},
        ),
        migrations.AddField(
            model_name="usersubscription",
            name="end_station",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="subscription_ends",
                to="stations.station",
            ),
        ),
        migrations.AddField(
            model_name="usersubscription",
            name="plan",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to="tickets.subscriptionplan",
            ),
        ),
        migrations.AddField(
            model_name="usersubscription",
            name="start_station",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="subscription_starts",
                to="stations.station",
            ),
        ),
        migrations.AddField(
            model_name="usersubscription",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="subscriptions",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddIndex(
            model_name="subscriptionplan",
            index=models.Index(fields=["type"], name="tickets_sub_type_b751db_idx"),
        ),
        migrations.AddField(
            model_name="stationzone",
            name="station",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="zone",
                to="stations.station",
            ),
        ),
        migrations.AddIndex(
            model_name="usersubscription",
            index=models.Index(
                fields=["user", "status"], name="tickets_use_user_id_becfb9_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="usersubscription",
            index=models.Index(
                fields=["start_date", "end_date"], name="tickets_use_start_d_cc0e5f_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="usersubscription",
            index=models.Index(fields=["status"], name="tickets_use_status_d027a2_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="stationzone",
            unique_together={("station", "zone_number")},
        ),
    ]
