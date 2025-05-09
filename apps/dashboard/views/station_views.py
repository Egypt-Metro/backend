from django.views.generic import TemplateView
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.utils import timezone
import datetime
import json

from ..utils import DecimalEncoder

from ..services.analytics_service import AnalyticsService
from ..services.export_service import ExportService


@method_decorator(staff_member_required, name='dispatch')
class StationDashboardView(TemplateView):
    """Station analytics dashboard view"""
    template_name = 'admin/dashboard/station_dashboard.html'

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

        # Get station analytics data
        station_data = AnalyticsService.get_station_analytics(start_date, end_date)

        context.update({
            'stations_traffic': json.dumps(station_data['stations_traffic'], cls=DecimalEncoder),
            'popular_routes': json.dumps(station_data['popular_routes'], cls=DecimalEncoder),
            'day_of_week_usage': json.dumps(station_data['day_of_week_usage'], cls=DecimalEncoder),
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

            station_data = AnalyticsService.get_station_analytics(start_date, end_date)

            if data_type == 'stations_traffic':
                data = station_data['stations_traffic']
                filename = 'stations_traffic'
            elif data_type == 'popular_routes':
                data = station_data['popular_routes']
                filename = 'popular_routes'
            elif data_type == 'day_of_week_usage':
                data = station_data['day_of_week_usage']
                filename = 'day_of_week_usage'
            else:
                data = []
                filename = 'station_data'

            if export_type == 'excel':
                return ExportService.export_to_excel({data_type: data}, filename)
            else:
                return ExportService.export_to_csv(data, filename)

        return super().get(request, *args, **kwargs)
