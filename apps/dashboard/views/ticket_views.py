from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.utils import timezone
import datetime
import json

from ..services.analytics_service import AnalyticsService
from ..services.export_service import ExportService


@method_decorator(staff_member_required, name='dispatch')
class TicketDashboardView(TemplateView):
    """Ticket analytics dashboard view"""
    template_name = 'admin/dashboard/ticket_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get date parameters
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')

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

        # Get ticket analytics data
        ticket_data = AnalyticsService.get_ticket_analytics(start_date, end_date)

        context.update({
            'ticket_sales': json.dumps(ticket_data['ticket_sales']),
            'subscription_sales': json.dumps(ticket_data['subscription_sales']),
            'daily_trend': json.dumps(ticket_data['daily_trend']),
            'hourly_usage': json.dumps(ticket_data['hourly_usage']),
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d')
        })

        return context

    def post(self, request, *args, **kwargs):
        """Handle export requests"""
        if 'export' in request.POST:
            export_type = request.POST.get('export_type', 'csv')
            data_type = request.POST.get('data_type', '')

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

            ticket_data = AnalyticsService.get_ticket_analytics(start_date, end_date)

            if data_type == 'ticket_sales':
                data = ticket_data['ticket_sales']
                filename = 'ticket_sales'
            elif data_type == 'subscription_sales':
                data = ticket_data['subscription_sales']
                filename = 'subscription_sales'
            elif data_type == 'daily_trend':
                data = ticket_data['daily_trend']
                filename = 'daily_ticket_sales'
            elif data_type == 'hourly_usage':
                data = ticket_data['hourly_usage']
                filename = 'hourly_traffic'
            else:
                data = []
                filename = 'ticket_data'

            if export_type == 'excel':
                return ExportService.export_to_excel({data_type: data}, filename)
            else:
                return ExportService.export_to_csv(data, filename)

        return super().get(request, *args, **kwargs)
