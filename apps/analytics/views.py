from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from datetime import timedelta
from apps.stations.models import Station, Line
from .services import (
    get_station_analytics,
    get_line_analytics,
    get_daily_revenue_trend,
    get_ticket_status_analytics
)


class AnalyticsViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def station(self, request):
        """Get analytics for a specific station"""
        station_id = request.query_params.get('station_id')
        if not station_id:
            return Response(
                {"error": "station_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        try:
            analytics = get_station_analytics(station_id, start_date, end_date)
            return Response(analytics)
        except Station.DoesNotExist:
            return Response(
                {"error": "Station not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def line(self, request):
        """Get analytics for a specific line"""
        line_id = request.query_params.get('line_id')
        if not line_id:
            return Response(
                {"error": "line_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        try:
            analytics = get_line_analytics(line_id, start_date, end_date)
            return Response(analytics)
        except Line.DoesNotExist:
            return Response(
                {"error": "Line not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def daily_trend(self, request):
        """Get daily revenue trend"""
        days = request.query_params.get('days', 30)
        try:
            days = int(days)
            trend_data = get_daily_revenue_trend(days)
            return Response(trend_data)
        except ValueError:
            return Response(
                {"error": "days parameter must be an integer"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get overall analytics summary"""
        # Default to last 30 days if no date range specified
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)

        try:
            # Get analytics for all lines
            lines = Line.objects.all()
            line_analytics = []

            for line in lines:
                line_data = get_line_analytics(line.id, start_date, end_date)
                line_analytics.append(line_data)

            # Get overall trend
            trend_data = get_daily_revenue_trend(days)

            return Response({
                'period': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'days': days
                },
                'lines': line_analytics,
                'daily_trend': trend_data
            })
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@action(detail=False, methods=['get'])
def tickets(self, request):
    """Get analytics about tickets by status and type"""
    try:
        analytics = get_ticket_status_analytics()
        return Response(analytics)
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
