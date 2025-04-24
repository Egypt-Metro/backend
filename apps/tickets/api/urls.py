from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.scanner_views import ScannerProcessView
from .views.ticket_views import TicketViewSet
from .views.subscription_views import SubscriptionViewSet

app_name = 'tickets'

router = DefaultRouter()
router.register(r'', TicketViewSet, basename='ticket')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('', include(router.urls)),
    path('scanner/process/', ScannerProcessView.as_view(), name='scanner-process'),
]
