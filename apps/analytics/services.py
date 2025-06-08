from decimal import Decimal
import logging
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.utils import timezone
from apps.tickets.models import Ticket, UserSubscription
from apps.stations.models import Station, Line
from .models import StationAnalytics, LineAnalytics, TicketUsageRecord, SubscriptionUsageRecord, DailyAnalytics

logger = logging.getLogger(__name__)


def record_ticket_usage(ticket_id, station_id, usage_type='ENTRY'):
    """
    Record a ticket being used at a station and update all relevant analytics

    Args:
        ticket_id: ID of the ticket
        station_id: ID of the station where ticket was used
        usage_type: 'ENTRY' or 'EXIT'
    """
    with transaction.atomic():
        ticket = Ticket.objects.get(id=ticket_id)
        station = Station.objects.get(id=station_id)

        # Check if we've already recorded this ticket's usage to avoid duplicates
        existing_record = TicketUsageRecord.objects.filter(
            ticket=ticket,
            station=station,
            usage_type=usage_type
        ).exists()

        if existing_record:
            logger.info(f"Skipping duplicate {usage_type} record for ticket {ticket.id} at station {station.name}")
            return None

        # Get or create station analytics
        station_analytics, _ = StationAnalytics.objects.get_or_create(station=station)

        # Get line for this station
        lines = station.lines.all()
        if not lines.exists():
            raise ValueError(f"Station {station.name} is not associated with any line")

        # For simplicity, attribute to first line if station serves multiple lines
        line = lines.first()

        # Get or create line analytics
        line_analytics, _ = LineAnalytics.objects.get_or_create(line=line)

        # Record the usage
        usage_record = TicketUsageRecord.objects.create(
            ticket=ticket,
            station=station,
            line=line,
            revenue_amount=ticket.price,
            timestamp=timezone.now(),
            usage_type=usage_type
        )

        # Only attribute revenue for ENTRY events to avoid double counting
        if usage_type == 'ENTRY':
            # Update station analytics
            station_analytics.total_revenue += ticket.price
            station_analytics.ticket_revenue += ticket.price
            station_analytics.tickets_scanned += 1
            station_analytics.total_entries += 1
            station_analytics.save()

            # Update line analytics
            line_analytics.total_revenue += ticket.price
            line_analytics.ticket_revenue += ticket.price
            line_analytics.tickets_scanned += 1
            line_analytics.total_entries += 1
            line_analytics.save()

            # Update daily analytics
            today = timezone.now().date()
            daily_analytics, _ = DailyAnalytics.objects.get_or_create(date=today)
            daily_analytics.total_revenue += ticket.price
            daily_analytics.ticket_revenue += ticket.price
            daily_analytics.tickets_scanned += 1
            daily_analytics.total_entries += 1
            daily_analytics.save()

        return usage_record


def record_subscription_usage(subscription_id, station_id):
    """
    Record a subscription being used at a station and update all relevant analytics
    """
    with transaction.atomic():
        subscription = UserSubscription.objects.get(id=subscription_id)
        station = Station.objects.get(id=station_id)

        # Calculate per-use revenue (divide subscription price by total allowed uses)
        # This is an estimation for revenue attribution
        subscription_plan = subscription.plan
        if subscription_plan.price:
            # For monthly subscriptions, assume 30 uses per month
            if subscription_plan.type == 'MONTHLY':
                per_use_revenue = subscription_plan.price / Decimal(30)
            elif subscription_plan.type == 'QUARTERLY':
                per_use_revenue = subscription_plan.price / Decimal(90)
            elif subscription_plan.type == 'ANNUAL':
                per_use_revenue = subscription_plan.price / Decimal(365)
            else:
                per_use_revenue = subscription_plan.price / Decimal(30)  # default
        else:
            per_use_revenue = Decimal(0)

        # Get or create station analytics
        station_analytics, _ = StationAnalytics.objects.get_or_create(station=station)

        # Get line for this station
        lines = station.lines.all()
        if not lines.exists():
            raise ValueError(f"Station {station.name} is not associated with any line")

        # For simplicity, attribute to first line if station serves multiple lines
        line = lines.first()

        # Get or create line analytics
        line_analytics, _ = LineAnalytics.objects.get_or_create(line=line)

        # Record the usage
        usage_record = SubscriptionUsageRecord.objects.create(
            subscription=subscription,
            station=station,
            line=line,
            revenue_amount=per_use_revenue,
            timestamp=timezone.now()
        )

        # Update station analytics
        station_analytics.total_revenue += per_use_revenue
        station_analytics.subscription_revenue += per_use_revenue
        station_analytics.subscriptions_used += 1
        station_analytics.total_entries += 1
        station_analytics.save()

        # Update line analytics
        line_analytics.total_revenue += per_use_revenue
        line_analytics.subscription_revenue += per_use_revenue
        line_analytics.subscriptions_used += 1
        line_analytics.total_entries += 1
        line_analytics.save()

        # Update daily analytics
        today = timezone.now().date()
        daily_analytics, _ = DailyAnalytics.objects.get_or_create(date=today)
        daily_analytics.total_revenue += per_use_revenue
        daily_analytics.subscription_revenue += per_use_revenue
        daily_analytics.subscriptions_used += 1
        daily_analytics.total_entries += 1
        daily_analytics.save()

        return usage_record


def get_station_analytics(station_id, start_date=None, end_date=None):
    """Get detailed analytics for a specific station with optional date filtering"""
    station = Station.objects.get(id=station_id)

    # Base queries
    ticket_query = TicketUsageRecord.objects.filter(station=station)
    subscription_query = SubscriptionUsageRecord.objects.filter(station=station)

    # Apply date filtering if provided
    if start_date:
        ticket_query = ticket_query.filter(timestamp__date__gte=start_date)
        subscription_query = subscription_query.filter(timestamp__date__gte=start_date)

    if end_date:
        ticket_query = ticket_query.filter(timestamp__date__lte=end_date)
        subscription_query = subscription_query.filter(timestamp__date__lte=end_date)

    # Calculate metrics
    ticket_revenue = ticket_query.aggregate(total=Sum('revenue_amount'))['total'] or 0
    subscription_revenue = subscription_query.aggregate(total=Sum('revenue_amount'))['total'] or 0
    tickets_count = ticket_query.count()
    subscription_uses = subscription_query.count()

    # Get hourly distribution for peak analysis
    hourly_distribution = (
        ticket_query.values('timestamp__hour')
        .annotate(count=Count('id'))
        .order_by('timestamp__hour')
    )

    return {
        'station': station.name,
        'total_revenue': ticket_revenue + subscription_revenue,
        'ticket_revenue': ticket_revenue,
        'subscription_revenue': subscription_revenue,
        'tickets_scanned': tickets_count,
        'subscription_uses': subscription_uses,
        'total_entries': tickets_count + subscription_uses,
        'hourly_distribution': list(hourly_distribution),
    }


def get_line_analytics(line_id, start_date=None, end_date=None):
    """Get detailed analytics for a specific line with optional date filtering"""
    line = Line.objects.get(id=line_id)

    # Get all stations for this line
    stations = Station.objects.filter(lines=line)

    # Base queries - tickets and subscriptions used at any station on this line
    ticket_query = TicketUsageRecord.objects.filter(line=line)
    subscription_query = SubscriptionUsageRecord.objects.filter(line=line)

    # Apply date filtering if provided
    if start_date:
        ticket_query = ticket_query.filter(timestamp__date__gte=start_date)
        subscription_query = subscription_query.filter(timestamp__date__gte=start_date)

    if end_date:
        ticket_query = ticket_query.filter(timestamp__date__lte=end_date)
        subscription_query = subscription_query.filter(timestamp__date__lte=end_date)

    # Calculate metrics
    ticket_revenue = ticket_query.aggregate(total=Sum('revenue_amount'))['total'] or 0
    subscription_revenue = subscription_query.aggregate(total=Sum('revenue_amount'))['total'] or 0
    tickets_count = ticket_query.count()
    subscription_uses = subscription_query.count()

    # Get per-station breakdown
    station_breakdown = []
    for station in stations:
        station_ticket_revenue = ticket_query.filter(station=station).aggregate(
            total=Sum('revenue_amount')
        )['total'] or 0

        station_subscription_revenue = subscription_query.filter(station=station).aggregate(
            total=Sum('revenue_amount')
        )['total'] or 0

        station_breakdown.append({
            'station': station.name,
            'total_revenue': station_ticket_revenue + station_subscription_revenue,
            'ticket_revenue': station_ticket_revenue,
            'subscription_revenue': station_subscription_revenue,
            'tickets_scanned': ticket_query.filter(station=station).count(),
            'subscription_uses': subscription_query.filter(station=station).count(),
        })

    return {
        'line': line.name,
        'total_revenue': ticket_revenue + subscription_revenue,
        'ticket_revenue': ticket_revenue,
        'subscription_revenue': subscription_revenue,
        'tickets_scanned': tickets_count,
        'subscription_uses': subscription_uses,
        'total_entries': tickets_count + subscription_uses,
        'station_breakdown': station_breakdown,
    }


def get_daily_revenue_trend(days=30):
    """Get daily revenue trend for the last specified number of days"""
    end_date = timezone.now().date()
    start_date = end_date - timezone.timedelta(days=days)

    daily_analytics = DailyAnalytics.objects.filter(
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date')

    return [
        {
            'date': analytics.date,
            'total_revenue': analytics.total_revenue,
            'ticket_revenue': analytics.ticket_revenue,
            'subscription_revenue': analytics.subscription_revenue,
            'total_entries': analytics.total_entries,
        }
        for analytics in daily_analytics
    ]


def get_ticket_status_analytics():
    """Get analytics on tickets by status"""
    tickets_by_status = Ticket.objects.values('status').annotate(
        count=Count('id'),
        revenue=Sum('price')
    )

    # Get tickets by type
    tickets_by_type = Ticket.objects.values('ticket_type').annotate(
        count=Count('id'),
        revenue=Sum('price'),
        active_count=Count('id', filter=Q(status__iexact='active')),
        used_count=Count('id', filter=Q(status__iexact='used')),
        expired_count=Count('id', filter=Q(status__iexact='expired'))
    )

    return {
        'by_status': list(tickets_by_status),
        'by_type': list(tickets_by_type),
        'total_tickets': Ticket.objects.count(),
        'total_revenue': Ticket.objects.aggregate(total=Sum('price'))['total'] or 0,
    }
