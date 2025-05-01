from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.scanner_views import ScannerProcessView
from .views.ticket_views import TicketViewSet
from .views.subscription_views import SubscriptionViewSet
from .views.gate_views import GateStatusView

app_name = 'tickets'

router = DefaultRouter()
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')
router.register(r'', TicketViewSet, basename='ticket')

urlpatterns = [
    path('gate-status/', GateStatusView.as_view(), name='gate-status'),
    path('scanner/process/', ScannerProcessView.as_view(), name='scanner-process'),
    path('', include(router.urls)),
]
