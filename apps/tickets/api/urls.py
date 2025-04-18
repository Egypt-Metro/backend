from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.ticket_views import TicketViewSet
from .views.subscription_views import SubscriptionViewSet

router = DefaultRouter()
router.register(r'tickets', TicketViewSet, basename='ticket')
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('', include(router.urls)),
]
