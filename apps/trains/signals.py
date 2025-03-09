# apps/trains/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.trains.constants.choices import CARS_PER_TRAIN
from .models.train import Train, TrainCar


@receiver(post_save, sender=Train)
def create_train_cars(sender, instance, created, **kwargs):
    """Create cars for new trains"""
    if created:
        for car_number in range(1, CARS_PER_TRAIN + 1):
            TrainCar.objects.create(
                train=instance,
                car_number=car_number,
                has_camera=(car_number == instance.camera_car_number)
            )
