# apps/routes/urls.py

from django.urls import path
from .views import RouteView

urlpatterns = [
    path('find/', RouteView.as_view(), name='find_route'),
]
