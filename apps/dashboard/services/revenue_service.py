# apps/dashboard/services/revenue_service.py
from datetime import date
from django.db.models import Sum, Avg
from django.utils import timezone
from typing import Dict, List, Any, Optional
from apps.stations.models import Line
from apps.dashboard.models import RevenueMetrics


class RevenueService:
    """
    Comprehensive revenue tracking and analysis
    """
    @classmethod
    def aggregate_revenue_metrics(
        cls,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        period_type: str = 'daily'
    ) -> List[Dict[str, Any]]:
        """
        Aggregate revenue metrics across lines
        """
        if not start_date:
            start_date = timezone.now().date() - timezone.timedelta(days=30)
        if not end_date:
            end_date = timezone.now().date()

        # Aggregate metrics
        revenue_data = RevenueMetrics.objects.filter(
            date__range=[start_date, end_date],
            period_type=period_type
        ).values('line__name').annotate(
            total_revenue=Sum('total_revenue'),
            ticket_sales=Sum('ticket_sales'),
            subscription_revenue=Sum('subscription_revenue'),
            subscription_count=Sum('subscription_count')
        )

        return list(revenue_data)

    @classmethod
    def get_line_revenue_breakdown(
        cls,
        line: Optional[Line] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Detailed revenue breakdown for a specific line
        """
        # Default to last 30 days if no dates provided
        if not start_date:
            start_date = timezone.now().date() - timezone.timedelta(days=30)
        if not end_date:
            end_date = timezone.now().date()

        # Query base
        metrics = RevenueMetrics.objects.filter(
            date__range=[start_date, end_date]
        )

        # Filter by line if provided
        if line:
            metrics = metrics.filter(line=line)

        # Aggregate metrics
        breakdown = metrics.aggregate(
            total_revenue=Sum('total_revenue'),
            total_ticket_sales=Sum('ticket_sales'),
            total_subscription_revenue=Sum('subscription_revenue'),
            total_subscriptions=Sum('subscription_count'),
            avg_ticket_price=Avg('avg_ticket_price')
        )

        return {
            'line': line.name if line else 'All Lines',
            'date_range': {
                'start': start_date,
                'end': end_date
            },
            **breakdown
        }

    @classmethod
    def predict_future_revenue(
        cls,
        prediction_horizon: int = 30
    ) -> Dict[str, float]:
        """
        Advanced revenue prediction
        """
        # Get historical revenue data
        historical_data = cls.get_line_revenue_breakdown()

        # Simple linear projection
        avg_daily_revenue = (
            historical_data.get('total_revenue', 0)
            / prediction_horizon
        )

        predicted_revenue = avg_daily_revenue * prediction_horizon

        return {
            'historical_avg_daily_revenue': avg_daily_revenue,
            'predicted_revenue': predicted_revenue,
            'confidence_interval': 0.85  # Example confidence level
        }

    @classmethod
    def generate_periodic_metrics(cls):
        """
        Generate periodic revenue metrics
        """
        # Get all lines
        lines = Line.objects.all()

        for line in lines:
            # Daily metrics
            cls._create_line_metrics(line, 'daily')

            # Weekly metrics (if it's the end of the week)
            if timezone.now().weekday() == 6:  # Sunday
                cls._create_line_metrics(line, 'weekly')

            # Monthly metrics (if it's the last day of the month)
            current_date = timezone.now().date()
            last_day_of_month = current_date.replace(day=1) - timezone.timedelta(days=1)

            if current_date == last_day_of_month:
                cls._create_line_metrics(line, 'monthly')

    @classmethod
    def _create_line_metrics(cls, line: Line, period_type: str):
        """
        Create metrics for a specific line and period
        """
        # Calculate metrics
        ticket_sales = cls._calculate_ticket_sales(line, period_type)
        subscription_data = cls._calculate_subscription_data(line, period_type)

        # Create metrics record
        RevenueMetrics.objects.create(
            line=line,
            period_type=period_type,
            total_revenue=ticket_sales['total_revenue'] + subscription_data['revenue'],
            ticket_sales=ticket_sales['count'],
            subscription_revenue=subscription_data['revenue'],
            subscription_count=subscription_data['count'],
            avg_ticket_price=ticket_sales['avg_price']
        )

    @classmethod
    def _calculate_ticket_sales(cls, line: Line, period_type: str) -> Dict[str, float]:
        """
        Calculate ticket sales for a line

        This is a placeholder method. You should implement actual logic
        to calculate ticket sales based on your specific tracking mechanism.
        """
        from apps.stations.models import Station  # Avoid circular import

        # Example implementation (modify as per your actual data model)
        ticket_sales = Station.objects.filter(lines=line).aggregate(
            total_revenue=Sum('ticket_sales__price'),
            count=Sum('ticket_sales__count')
        )

        return {
            'total_revenue': ticket_sales['total_revenue'] or 0,
            'count': ticket_sales['count'] or 0,
            'avg_price': (ticket_sales['total_revenue'] / ticket_sales['count'])
            if ticket_sales['count'] else 0
        }

    @classmethod
    def _calculate_subscription_data(cls, line: Line, period_type: str) -> Dict[str, float]:
        """
        Calculate subscription data for a line

        This is a placeholder method. You should implement actual logic
        to calculate subscription data based on your specific tracking mechanism.
        """
        from apps.users.models import Subscription  # Avoid circular import

        # Example implementation (modify as per your actual data model)
        subscription_data = Subscription.objects.filter(line=line).aggregate(
            revenue=Sum('price'),
            count=Sum('active_subscriptions')
        )

        return {
            'revenue': subscription_data['revenue'] or 0,
            'count': subscription_data['count'] or 0
        }
