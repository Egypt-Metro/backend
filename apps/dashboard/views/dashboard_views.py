from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.utils import timezone
import datetime

from ..utils import json_serialize
from ..services.analytics_service import AnalyticsService
from ..services.export_service import ExportService


@method_decorator(staff_member_required, name='dispatch')
class DashboardView(TemplateView):
    """Main admin dashboard view"""
    template_name = 'admin/dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get date ranges
        date_ranges = AnalyticsService.get_date_ranges()
        today = date_ranges['today']
        start_of_month = date_ranges['start_of_month']

        # Get summary metrics
        revenue_data = AnalyticsService.get_revenue_overview(
            start_date=start_of_month,
            end_date=today
        )

        # Get top stations
        top_stations = AnalyticsService.get_top_stations(
            start_date=start_of_month,
            end_date=today,
            limit=5
        )

        # Get revenue by line
        revenue_by_line = AnalyticsService.get_revenue_by_line(
            start_date=start_of_month,
            end_date=today
        )

        # Get ticket analytics
        ticket_data = AnalyticsService.get_ticket_analytics(
            start_date=start_of_month,
            end_date=today
        )

        # Combine all data - use the custom JSON encoder for all data
        context.update({
            'revenue': revenue_data['summary'],
            'revenue_trend': json_serialize(revenue_data['daily_breakdown']),
            'top_stations': json_serialize(top_stations),
            'revenue_by_line': json_serialize(revenue_by_line),
            'ticket_sales': json_serialize(ticket_data['ticket_sales']),
            'subscription_sales': json_serialize(ticket_data['subscription_sales']),
            'hourly_usage': json_serialize(ticket_data['hourly_usage'])
        })

        return context

    def post(self, request, *args, **kwargs):
        """Handle export requests"""
        if 'export' in request.POST:
            export_type = request.POST.get('export_type', 'csv')
            data_type = request.POST.get('data_type', '')

            # Get date parameters
            start_date_str = request.POST.get('start_date')
            end_date_str = request.POST.get('end_date')

            try:
                if start_date_str:
                    start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
                else:
                    start_date = timezone.now().date() - datetime.timedelta(days=30)

                if end_date_str:
                    end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
                else:
                    end_date = timezone.now().date()
            except ValueError:
                start_date = timezone.now().date() - datetime.timedelta(days=30)
                end_date = timezone.now().date()

            # Get data for export
            if data_type == 'revenue':
                data = AnalyticsService.get_revenue_overview(start_date, end_date)['daily_breakdown']
                filename = 'revenue_data'
            elif data_type == 'stations':
                data = AnalyticsService.get_top_stations(start_date, end_date, limit=50)
                filename = 'station_data'
            elif data_type == 'lines':
                data = AnalyticsService.get_revenue_by_line(start_date, end_date)
                filename = 'line_revenue'
            elif data_type == 'tickets':
                data = AnalyticsService.get_ticket_analytics(start_date, end_date)['ticket_sales']
                filename = 'ticket_sales'
            elif data_type == 'subscriptions':
                data = AnalyticsService.get_ticket_analytics(start_date, end_date)['subscription_sales']
                filename = 'subscription_sales'
            else:
                data = []
                filename = 'metro_data'

            # Export data
            if export_type == 'excel':
                return ExportService.export_to_excel({data_type: data}, filename)
            else:  # Default to CSV
                return ExportService.export_to_csv(data, filename)

        return super().get(request, *args, **kwargs)
