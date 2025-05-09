# Generated by Django 4.2.16 on 2025-02-08 19:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('stations', '0002_connectingstation'),
    ]

    operations = [
        migrations.CreateModel(
            name='PrecomputedRoute',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('distance', models.FloatField(help_text='Distance in meters')),
                ('duration', models.FloatField(help_text='Estimated travel time in minutes')),
                ('path', models.JSONField(help_text='Ordered list of station IDs forming the route')),
                ('end_station', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='route_ends', to='stations.station')),
                ('start_station', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='route_starts', to='stations.station')),
            ],
            options={
                'indexes': [models.Index(fields=['start_station', 'end_station'], name='routes_prec_start_s_d2a4df_idx')],
                'unique_together': {('start_station', 'end_station')},
            },
        ),
    ]
