import csv
import io
from datetime import timedelta
from django.utils import timezone
from django.http import HttpResponse
from .models import StationAnalytics, LineAnalytics, TicketUsageRecord, SubscriptionUsageRecord


def generate_station_revenue_report(start_date=None, end_date=None):
    """Generate a CSV report of revenue by station"""
    if not start_date:
        start_date = timezone.now().date() - timedelta(days=30)
    if not end_date:
        end_date = timezone.now().date()

    # Get data
    stations = StationAnalytics.objects.all().select_related('station')

    # Create CSV
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    # Write header
    writer.writerow([
        'Station ID', 'Station Name', 'Lines',
        'Total Revenue', 'Ticket Revenue', 'Subscription Revenue',
        'Tickets Scanned', 'Subscription Uses', 'Total Entries'
    ])

    # Write data rows
    for station_analytics in stations:
        station = station_analytics.station
        lines = ', '.join([line.name for line in station.lines.all()])

        writer.writerow([
            station.id,
            station.name,
            lines,
            station_analytics.total_revenue,
            station_analytics.ticket_revenue,
            station_analytics.subscription_revenue,
            station_analytics.tickets_scanned,
            station_analytics.subscriptions_used,
            station_analytics.total_entries,
        ])

    # Create response
    response = HttpResponse(buffer.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="station_revenue_{start_date}_to_{end_date}.csv"'

    return response


def generate_line_revenue_report(start_date=None, end_date=None):
    """Generate a CSV report of revenue by line"""
    if not start_date:
        start_date = timezone.now().date() - timedelta(days=30)
    if not end_date:
        end_date = timezone.now().date()

    # Get data
    lines = LineAnalytics.objects.all().select_related('line')

    # Create CSV
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    # Write header
    writer.writerow([
        'Line ID', 'Line Name',
        'Total Revenue', 'Ticket Revenue', 'Subscription Revenue',
        'Tickets Scanned', 'Subscription Uses', 'Total Entries'
    ])

    # Write data rows
    for line_analytics in lines:
        line = line_analytics.line

        writer.writerow([
            line.id,
            line.name,
            line_analytics.total_revenue,
            line_analytics.ticket_revenue,
            line_analytics.subscription_revenue,
            line_analytics.tickets_scanned,
            line_analytics.subscriptions_used,
            line_analytics.total_entries,
        ])

    # Create response
    response = HttpResponse(buffer.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="line_revenue_{start_date}_to_{end_date}.csv"'

    return response


def generate_daily_usage_report(start_date=None, end_date=None):
    """Generate a detailed daily usage report"""
    if not start_date:
        start_date = timezone.now().date() - timedelta(days=30)
    if not end_date:
        end_date = timezone.now().date()

    # Fetch ticket usage data
    ticket_usages = TicketUsageRecord.objects.filter(
        timestamp__date__gte=start_date,
        timestamp__date__lte=end_date
    ).select_related('station', 'line', 'ticket')

    # Create CSV
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    # Write header
    writer.writerow([
        'Date', 'Time', 'Ticket/Subscription ID', 'Type',
        'Station', 'Line', 'Revenue Amount'
    ])

    # Write ticket usage data
    for usage in ticket_usages:
        writer.writerow([
            usage.timestamp.date(),
            usage.timestamp.time(),
            usage.ticket.id,
            'Ticket',
            usage.station.name,
            usage.line.name,
            usage.revenue_amount
        ])

    # Fetch subscription usage data
    subscription_usages = SubscriptionUsageRecord.objects.filter(
        timestamp__date__gte=start_date,
        timestamp__date__lte=end_date
    ).select_related('station', 'line', 'subscription')

    # Write subscription usage data
    for usage in subscription_usages:
        writer.writerow([
            usage.timestamp.date(),
            usage.timestamp.time(),
            usage.subscription.id,
            'Subscription',
            usage.station.name,
            usage.line.name,
            usage.revenue_amount
        ])

    # Create response
    response = HttpResponse(buffer.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="daily_usage_{start_date}_to_{end_date}.csv"'

    return response
