# apps/dashboard/services/performance_service.py
from django.db.models import Avg, Sum, F
from django.utils import timezone
from typing import Dict, List
from ..utils.model_loader import load_model


class PerformanceService:
    """
    Comprehensive metro line performance tracking
    """
    @classmethod
    def get_line_performance(
        cls,
        start_date: timezone.date = None,
        end_date: timezone.date = None
    ) -> List[Dict]:
        """
        Detailed performance metrics for metro lines
        """
        # Dynamically load Trip model
        Trip = load_model('trips', 'Trip')

        # Default to last 30 days if no dates provided
        if not start_date:
            start_date = timezone.now() - timezone.timedelta(days=30)
        if not end_date:
            end_date = timezone.now()

        performance_data = Trip.objects.filter(
            date__range=[start_date, end_date]
        ).annotate(
            line=F('metro_line')
        ).values('line').annotate(
            avg_passengers=Avg('passenger_count'),
            total_passengers=Sum('passenger_count'),
            avg_delay=Avg('delay_minutes'),
            total_trips=Sum('trip_count')
        )

        return list(performance_data)

    @classmethod
    def identify_bottlenecks(
        cls,
        performance_data: List[Dict] = None
    ) -> Dict:
        """
        Identify performance bottlenecks
        """
        if not performance_data:
            performance_data = cls.get_line_performance()

        # Find lines with lowest performance
        bottlenecks = sorted(
            performance_data,
            key=lambda x: x['avg_passengers']
        )[:3]  # Top 3 lowest performing lines

        return {
            'bottlenecks': bottlenecks,
            'recommendations': cls._generate_recommendations(bottlenecks)
        }

    @classmethod
    def _generate_recommendations(
        cls,
        bottlenecks: List[Dict]
    ) -> List[str]:
        """
        Generate performance improvement recommendations
        """
        recommendations = []
        for line in bottlenecks:
            recommendation = (
                f"Line {line['line']}: Increase capacity, "
                f"optimize scheduling, reduce average delay"
            )
            recommendations.append(recommendation)

        return recommendations
