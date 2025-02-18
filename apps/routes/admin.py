from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from apps.routes.models import Route
from apps.stations.models import Station


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = (
        'start_station',
        'end_station',
        'primary_line',
        'number_of_stations',
        'total_time',
    )

    list_filter = (
        'is_active',
        'primary_line',
        'created_at',
    )

    search_fields = (
        'start_station__name',
        'end_station__name',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'number_of_stations',
        'path',
        'interchanges',
    )

    change_list_template = 'admin/routes/route/change_list.html'

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('search-stations/', self.search_stations, name='search-stations'),
            path('get-route-details/', self.get_route_details, name='get-route-details'),
        ]
        return custom_urls + urls

    def search_stations(self, request):
        """API endpoint for station search"""
        term = request.GET.get('term', '')
        stations = Station.objects.filter(name__icontains=term).values('id', 'name')
        return JsonResponse(list(stations), safe=False)

    def get_route_details(self, request):
        """Get route details for selected stations"""
        start_id = request.GET.get('start')
        end_id = request.GET.get('end')

        try:
            route = Route.objects.get(
                start_station_id=start_id,
                end_station_id=end_id
            )
            return JsonResponse({
                'success': True,
                'data': {
                    'primary_line': str(route.primary_line),
                    'number_of_stations': route.number_of_stations,
                    'total_time': str(route.total_time),
                    'path': route.path,
                    'interchanges': route.interchanges
                }
            })
        except Route.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'No route found for selected stations'
            })
