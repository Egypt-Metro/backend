# apps/dashboard/services/report_service.py

import os
import pandas as pd
from django.conf import settings
from django.utils import timezone
from typing import Dict, Any
from django.db.models import Avg, Sum

from apps.dashboard.utils.model_loader import load_model


class ReportService:
    """
    Comprehensive report generation service
    """
    @classmethod
    def generate_report(cls, report_instance):
        """
        Generate reports with multiple format support
        """
        try:
            report_methods = {
                'daily_passenger': cls._generate_passenger_report,
                'monthly_revenue': cls._generate_revenue_report,
                'line_performance': cls._generate_line_performance_report
            }

            generate_method = report_methods.get(
                report_instance.report_type,
                cls._generate_default_report
            )

            report_data = generate_method(
                report_instance.start_date,
                report_instance.end_date
            )

            file_paths = cls._save_report_formats(
                report_data,
                report_instance.report_type
            )

            report_instance.file_path = file_paths['xlsx']
            report_instance.save()

            return file_paths

        except Exception as e:
            cls._log_report_error(e, report_instance)
            raise

    @classmethod
    def _generate_passenger_report(
        cls,
        start_date: timezone.date,
        end_date: timezone.date
    ) -> Dict[str, Any]:
        """
        Generate detailed passenger report
        """
        # Dynamically load Trip model
        Trip = load_model('trips', 'Trip')

        passenger_data = Trip.objects.filter(
            date__range=[start_date, end_date]
        ).values('metro_line', 'date').annotate(
            total_passengers=Sum('passenger_count')
        )

        return {
            'title': 'Passenger Report',
            'data': list(passenger_data)
        }

    @classmethod
    def _generate_revenue_report(
        cls,
        start_date: timezone.date,
        end_date: timezone.date
    ) -> Dict[str, Any]:
        """
        Generate comprehensive revenue report
        """
        # Dynamically load Trip model
        Trip = load_model('trips', 'Trip')

        revenue_data = Trip.objects.filter(
            date__range=[start_date, end_date]
        ).values('metro_line', 'date').annotate(
            total_revenue=Sum('ticket_price')
        )

        return {
            'title': 'Revenue Report',
            'data': list(revenue_data)
        }

    @classmethod
    def _generate_line_performance_report(
        cls,
        start_date: timezone.date,
        end_date: timezone.date
    ) -> Dict[str, Any]:
        """
        Generate line performance report
        """
        # Dynamically load Trip model
        Trip = load_model('trips', 'Trip')

        performance_data = Trip.objects.filter(
            date__range=[start_date, end_date]
        ).values('metro_line').annotate(
            avg_passengers=Avg('passenger_count'),
            total_revenue=Sum('ticket_price')
        )

        return {
            'title': 'Line Performance Report',
            'data': list(performance_data)
        }

    @classmethod
    def _generate_default_report(
        cls,
        start_date: timezone.date,
        end_date: timezone.date
    ) -> Dict[str, Any]:
        """
        Fallback default report generation
        """
        return {
            'title': 'Default Report',
            'data': []
        }

    @classmethod
    def _save_report_formats(
        cls,
        report_data: Dict[str, Any],
        report_type: str
    ) -> Dict[str, str]:
        """
        Save report in multiple formats
        """
        # Create report directory if not exists
        report_dir = os.path.join(
            settings.REPORT_STORAGE_PATH,
            report_type
        )
        os.makedirs(report_dir, exist_ok=True)

        # Generate unique filename
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"{report_type}_{timestamp}"

        # Excel report
        xlsx_path = os.path.join(
            report_dir,
            f"{base_filename}.xlsx"
        )
        df = pd.DataFrame(report_data['data'])
        df.to_excel(xlsx_path, index=False)

        # CSV report
        csv_path = os.path.join(
            report_dir,
            f"{base_filename}.csv"
        )
        df.to_csv(csv_path, index=False)

        return {
            'xlsx': xlsx_path,
            'csv': csv_path
        }

    @classmethod
    def _log_report_error(
        cls,
        error: Exception,
        report_instance: Any
    ):
        """
        Log report generation errors
        """
        # Implement logging mechanism
        pass
