from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views.wallet_views import WalletViewSet
from .views.transaction_views import TransactionViewSet
from .views.payment_method_views import PaymentMethodViewSet

router = DefaultRouter()
router.register(r'wallet', WalletViewSet, basename='wallet')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'payment-methods', PaymentMethodViewSet, basename='payment-method')

urlpatterns = [
    path('', include(router.urls)),
]
