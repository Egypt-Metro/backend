# apps/dashboard/tasks/reporting_tasks.py

from celery import shared_task
from django.utils import timezone
from ..models import ReportGeneration
from ..services.report_service import ReportService


@shared_task
def generate_periodic_reports():
    """
    Generate periodic reports automatically
    """
    report_types = ['daily', 'weekly', 'monthly']

    for report_type in report_types:
        report = ReportGeneration.objects.create(
            report_type=report_type,
            start_date=timezone.now() - timezone.timedelta(days=30),
            end_date=timezone.now()
        )

        # Generate report using report service
        ReportService.generate_report(report)
