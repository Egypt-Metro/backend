from django.urls import path
from .views.dashboard_views import DashboardView
from .views.revenue_views import RevenueDashboardView
from .views.ticket_views import TicketDashboardView
from .views.station_views import StationDashboardView

app_name = 'dashboard'

urlpatterns = [
    path('', DashboardView.as_view(), name='index'),
    path('revenue/', RevenueDashboardView.as_view(), name='revenue'),
    path('tickets/', TicketDashboardView.as_view(), name='tickets'),
    path('stations/', StationDashboardView.as_view(), name='stations'),
]
