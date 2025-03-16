# apps/dashboard/tasks/analytics_tasks.py

from celery import shared_task
from django.utils import timezone
from django.core.cache import cache
from apps.dashboard.services.analytics_service import AnalyticsService
from apps.dashboard.models import AdminMetrics, ReportGeneration


@shared_task(bind=True)
def generate_comprehensive_metrics(self):
    """
    Advanced background task for metrics generation
    """
    try:
        today = timezone.now().date()

        # Fetch and process metrics
        passenger_trends = AnalyticsService.get_comprehensive_passenger_trends()
        revenue_predictions = AnalyticsService.predict_revenue()

        # Create metrics record
        metrics = AdminMetrics.objects.create(
            date=today,
            total_passengers=sum(trend['total_passengers'] for trend in passenger_trends),
            total_revenue=revenue_predictions['predicted_revenue'],
            line_performance=passenger_trends
        )

        # Cache results for quick access
        cache.set(f'metrics_{today}', metrics, timeout=86400)

        return metrics.id

    except Exception as exc:
        # Log error and potentially retry
        self.retry(exc=exc, countdown=60)


@shared_task
def generate_automated_reports():
    """
    Automated report generation task
    """
    report_types = ['daily_passenger', 'monthly_revenue']

    for report_type in report_types:
        ReportGeneration.objects.create(
            report_type=report_type,
            start_date=timezone.now() - timezone.timedelta(days=30),
            end_date=timezone.now()
        )
