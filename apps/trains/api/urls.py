# apps/trains/api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.train_views import TrainViewSet

router = DefaultRouter()
router.register(r'trains', TrainViewSet, basename='train')

urlpatterns = [
    path('', include(router.urls)),
]
