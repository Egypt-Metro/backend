from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.utils import timezone
import datetime

from ..utils import json_serialize
from ..services.analytics_service import AnalyticsService
from ..services.export_service import ExportService


@method_decorator(staff_member_required, name='dispatch')
class RevenueDashboardView(TemplateView):
    """Revenue dashboard view"""
    template_name = 'admin/dashboard/revenue_dashboard.html'

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

        # Get revenue data
        revenue_data = AnalyticsService.get_revenue_overview(start_date, end_date)

        # Get revenue by line
        revenue_by_line = AnalyticsService.get_revenue_by_line(start_date, end_date)

        # Get top performing stations
        top_stations = AnalyticsService.get_top_stations(
            start_date=start_date,
            end_date=end_date,
            limit=10
        )

        # Calculate previous period for comparison
        period_days = (end_date - start_date).days
        prev_end_date = start_date - datetime.timedelta(days=1)
        prev_start_date = prev_end_date - datetime.timedelta(days=period_days)

        prev_revenue = AnalyticsService.get_revenue_overview(prev_start_date, prev_end_date)

        # Calculate percentage changes
        current_total = revenue_data['summary']['total_revenue']
        prev_total = prev_revenue['summary']['total_revenue']

        if prev_total > 0:
            total_change_pct = ((current_total - prev_total) / prev_total) * 100
        else:
            total_change_pct = 100 if current_total > 0 else 0

        context.update({
            'revenue': revenue_data['summary'],
            'revenue_trend': json_serialize(revenue_data['daily_breakdown']),
            'revenue_by_line': json_serialize(revenue_by_line),
            'top_stations': json_serialize(top_stations),
            'period_comparison': {
                'current_period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                'prev_period': f"{prev_start_date.strftime('%Y-%m-%d')} to {prev_end_date.strftime('%Y-%m-%d')}",
                'current_total': current_total,
                'prev_total': prev_total,
                'change_pct': round(total_change_pct, 2)
            },
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

            if data_type == 'daily_revenue':
                data = AnalyticsService.get_revenue_overview(start_date, end_date)['daily_breakdown']
                filename = 'daily_revenue'
            elif data_type == 'line_revenue':
                data = AnalyticsService.get_revenue_by_line(start_date, end_date)
                filename = 'revenue_by_line'
            else:
                data = []
                filename = 'revenue_data'

            if export_type == 'excel':
                return ExportService.export_to_excel({data_type: data}, filename)
            else:
                return ExportService.export_to_csv(data, filename)

        return super().get(request, *args, **kwargs)
