# apps/dashboard/api/views.py

from datetime import timezone
from jsonschema import ValidationError
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from apps.dashboard.utils.validators import ReportValidator

from .serializers import (
    AdminMetricsSerializer,
    SystemAlertSerializer,
    ReportGenerationSerializer
)
from .permissions import IsSuperUserOrStaff, IsAdminWithSpecificPermissions
from ..models import AdminMetrics, SystemAlert, ReportGeneration
from ..services.analytics_service import AnalyticsService
from ..services.revenue_service import RevenueService


class AdminDashboardViewSet(viewsets.ModelViewSet):
    """
    Comprehensive admin dashboard viewset
    """
    queryset = AdminMetrics.objects.all()
    serializer_class = AdminMetricsSerializer
    permission_classes = [IsSuperUserOrStaff]

    @action(detail=False, methods=['GET'])
    def analytics(self, request):
        """
        Provide comprehensive analytics
        """
        try:
            analytics_data = {
                'passenger_trends': AnalyticsService.get_passenger_trends(),
                'revenue_predictions': AnalyticsService.predict_revenue()
            }
            return Response(analytics_data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SystemAlertViewSet(viewsets.ModelViewSet):
    """
    System alerts management
    """
    queryset = SystemAlert.objects.all()
    serializer_class = SystemAlertSerializer
    permission_classes = [IsAdminWithSpecificPermissions]


class ReportGenerationViewSet(viewsets.ModelViewSet):
    """
    Report generation management
    """
    queryset = ReportGeneration.objects.all()
    serializer_class = ReportGenerationSerializer
    permission_classes = [IsSuperUserOrStaff]


class RevenueViewSet(viewsets.ViewSet):
    """
    Revenue and sales tracking viewset
    """
    @action(detail=False, methods=['GET'])
    def revenue_breakdown(self, request):
        """
        Get comprehensive revenue breakdown
        """
        try:
            start_date = request.query_params.get('start_date')
            end_date = request.query_params.get('end_date')
            period = request.query_params.get('period', 'daily')

            # Validate dates if provided
            if start_date and end_date:
                try:
                    ReportValidator.validate_date_range(
                        timezone.datetime.strptime(start_date, '%Y-%m-%d').date(),
                        timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
                    )
                except ValidationError as e:
                    return Response(
                        {'error': str(e)},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            revenue_data = RevenueService.aggregate_revenue_metrics(
                start_date, end_date, period
            )

            return Response(revenue_data)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['GET'])
    def revenue_predictions(self, request):
        """
        Get revenue predictions
        """
        try:
            predictions = RevenueService.predict_future_revenue()
            return Response(predictions)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
