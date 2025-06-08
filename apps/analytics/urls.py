from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AnalyticsViewSet
from .reports import (
    generate_station_revenue_report,
    generate_line_revenue_report,
    generate_daily_usage_report
)

router = DefaultRouter()
router.register(r'', AnalyticsViewSet, basename='analytics')

urlpatterns = [
    path('', include(router.urls)),
    path('reports/station/', generate_station_revenue_report, name='station_report'),
    path('reports/line/', generate_line_revenue_report, name='line_report'),
    path('reports/daily_usage/', generate_daily_usage_report, name='daily_usage_report'),
]
