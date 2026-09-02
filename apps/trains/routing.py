# apps/trains/routing.py

from django.urls import re_path

from .consumers import TrainConsumer

websocket_urlpatterns = [
    re_path(r"ws/train/(?P<train_id>[^/]+)/$", TrainConsumer.as_asgi()),
]
