# apps/dashboard/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api.views import (
    AdminDashboardViewSet,
    SystemAlertViewSet,
    ReportGenerationViewSet,
    RevenueViewSet  # Add this import
)

router = DefaultRouter()
router.register(
    r'dashboard',
    AdminDashboardViewSet,
    basename='admin-dashboard'
)
router.register(
    r'alerts',
    SystemAlertViewSet,
    basename='system-alerts'
)
router.register(
    r'reports',
    ReportGenerationViewSet,
    basename='report-generation'
)
router.register(
    r'revenue',
    RevenueViewSet,
    basename='revenue'  # Add this line
)

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),

    # Additional custom dashboard routes can be added here
    path(
        'api/dashboard/metrics/',
        AdminDashboardViewSet.as_view({'get': 'list'}),
        name='dashboard-metrics'
    ),
    path(
        'api/revenue/breakdown/',
        RevenueViewSet.as_view({'get': 'revenue_breakdown'}),
        name='revenue-breakdown'
    ),
    path(
        'api/revenue/predictions/',
        RevenueViewSet.as_view({'get': 'revenue_predictions'}),
        name='revenue-predictions'
    )
]
