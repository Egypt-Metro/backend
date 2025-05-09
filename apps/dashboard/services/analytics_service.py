import datetime
from django.db.models import Sum, Count, F, Q
from django.db.models.functions import TruncDate, ExtractHour, ExtractWeekDay
from django.utils import timezone

from apps.tickets.models.ticket import Ticket
from apps.tickets.models.subscription import UserSubscription
from apps.stations.models import Station, Line
from apps.wallet.models.transaction import Transaction


class AnalyticsService:
    """Service for fetching analytics data without creating additional models"""

    @staticmethod
    def get_date_ranges():
        """Get common date ranges for analytics"""
        today = timezone.localtime().date()
        yesterday = today - datetime.timedelta(days=1)
        start_of_week = today - datetime.timedelta(days=today.weekday())
        start_of_month = today.replace(day=1)

        thirty_days_ago = today - datetime.timedelta(days=30)
        ninety_days_ago = today - datetime.timedelta(days=90)

        return {
            'today': today,
            'yesterday': yesterday,
            'start_of_week': start_of_week,
            'start_of_month': start_of_month,
            'thirty_days_ago': thirty_days_ago,
            'ninety_days_ago': ninety_days_ago,
        }

    @staticmethod
    def get_revenue_overview(start_date=None, end_date=None):
        """Get revenue overview for the given date range"""
        if not start_date:
            start_date = timezone.localtime().date() - datetime.timedelta(days=30)
        if not end_date:
            end_date = timezone.localtime().date()

        # Get revenue from transactions
        revenue_data = Transaction.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
            status='COMPLETED'
        ).aggregate(
            ticket_revenue=Sum(
                'amount',
                filter=Q(type='TICKET_PURCHASE'),
                default=0
            ),
            subscription_revenue=Sum(
                'amount',
                filter=Q(type='SUBSCRIPTION_PURCHASE'),
                default=0
            ),
            refunds=Sum(
                'amount',
                filter=Q(type='REFUND'),
                default=0
            ),
            wallet_deposits=Sum(
                'amount',
                filter=Q(type='DEPOSIT'),
                default=0
            )
        )

        # Calculate totals
        total_revenue = revenue_data['ticket_revenue'] + revenue_data['subscription_revenue']
        net_revenue = total_revenue - revenue_data['refunds']

        # Get daily breakdown
        daily_revenue = Transaction.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
            status='COMPLETED',
            type__in=['TICKET_PURCHASE', 'SUBSCRIPTION_PURCHASE', 'REFUND']
        ).annotate(
            date=TruncDate('created_at')
        ).values('date', 'type').annotate(
            amount=Sum('amount')
        ).order_by('date', 'type')

        # Transform to daily summary
        daily_summary = {}
        for entry in daily_revenue:
            date_str = entry['date'].strftime('%Y-%m-%d')
            if date_str not in daily_summary:
                daily_summary[date_str] = {
                    'date': date_str,
                    'ticket_revenue': 0,
                    'subscription_revenue': 0,
                    'refunds': 0
                }

            if entry['type'] == 'TICKET_PURCHASE':
                daily_summary[date_str]['ticket_revenue'] += entry['amount']
            elif entry['type'] == 'SUBSCRIPTION_PURCHASE':
                daily_summary[date_str]['subscription_revenue'] += entry['amount']
            elif entry['type'] == 'REFUND':
                daily_summary[date_str]['refunds'] += entry['amount']

        # Add calculated fields
        daily_breakdown = []
        for date_str, data in sorted(daily_summary.items()):
            total = data['ticket_revenue'] + data['subscription_revenue']
            net = total - data['refunds']
            daily_breakdown.append({
                'date': date_str,
                'ticket_revenue': data['ticket_revenue'],
                'subscription_revenue': data['subscription_revenue'],
                'refunds': data['refunds'],
                'total_revenue': total,
                'net_revenue': net
            })

        return {
            'summary': {
                'total_revenue': total_revenue,
                'net_revenue': net_revenue,
                'ticket_revenue': revenue_data['ticket_revenue'],
                'subscription_revenue': revenue_data['subscription_revenue'],
                'refunds': revenue_data['refunds'],
                'wallet_deposits': revenue_data['wallet_deposits'],
            },
            'daily_breakdown': daily_breakdown,
        }

    @staticmethod
    def get_revenue_by_line(start_date=None, end_date=None):
        """Get revenue breakdown by metro line using existing models"""
        if not start_date:
            start_date = timezone.localtime().date() - datetime.timedelta(days=30)
        if not end_date:
            end_date = timezone.localtime().date()

        # For ticket revenue, we can trace the entry station's line
        line_data = {}

        # Get all entry stations of tickets
        ticket_data = Ticket.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
            entry_station__isnull=False
        ).values(
            'entry_station__lines__id',
            'entry_station__lines__name',
            'entry_station__lines__color_code'  # CHANGE THIS from 'color' to 'color_code'
        ).annotate(
            revenue=Sum('price'),
            count=Count('id')
        )

        # Also update references below where you store the data
        for entry in ticket_data:
            line_id = entry['entry_station__lines__id']
            if line_id is None:
                continue

            if line_id not in line_data:
                line_data[line_id] = {
                    'id': line_id,
                    'name': entry['entry_station__lines__name'],
                    'color': entry['entry_station__lines__color_code'],  # CHANGE THIS to reference color_code
                    'ticket_revenue': 0,
                    'subscription_revenue': 0,
                    'passenger_count': 0
                }

            line_data[line_id]['ticket_revenue'] += entry['revenue'] or 0
            line_data[line_id]['passenger_count'] += entry['count'] or 0

        # For subscriptions, we need to distribute revenue across lines
        # This is a simplification - in reality this would be more complex
        subscription_total = UserSubscription.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).aggregate(
            total=Sum('plan__price', default=0)
        )['total'] or 0

        # Get line count for proportional allocation
        line_count = Line.objects.count()
        if line_count > 0:
            subscription_per_line = subscription_total / line_count

            # Allocate subscription revenue equally
            for line_id in line_data:
                line_data[line_id]['subscription_revenue'] = subscription_per_line

        # Convert to list and calculate total
        result = []
        for line_id, data in line_data.items():
            result.append({
                'name': data['name'],
                'color': data['color'],
                'ticket_revenue': data['ticket_revenue'],
                'subscription_revenue': data['subscription_revenue'],
                'total_revenue': data['ticket_revenue'] + data['subscription_revenue'],
                'passenger_count': data['passenger_count']
            })

        return sorted(result, key=lambda x: x['total_revenue'], reverse=True)

    @staticmethod
    def get_top_stations(start_date=None, end_date=None, limit=10):
        """Get top performing stations"""
        if not start_date:
            start_date = timezone.localtime().date() - datetime.timedelta(days=30)
        if not end_date:
            end_date = timezone.localtime().date()

        # Query stations with entry and exit counts
        stations = Station.objects.annotate(
            entry_count=Count(
                'ticket_entries',  # Changed from 'entry_tickets'
                filter=Q(
                    ticket_entries__created_at__date__gte=start_date,  # Changed from entry_tickets
                    ticket_entries__created_at__date__lte=end_date
                )
            ),
            exit_count=Count(
                'ticket_exits',  # Changed from 'exit_tickets'
                filter=Q(
                    ticket_exits__exit_time__date__gte=start_date,  # Changed from exit_tickets
                    ticket_exits__exit_time__date__lte=end_date
                )
            ),
            revenue=Sum(
                'ticket_entries__price',  # Changed from 'entry_tickets__price'
                filter=Q(
                    ticket_entries__created_at__date__gte=start_date,  # Changed from entry_tickets
                    ticket_entries__created_at__date__lte=end_date
                ),
                default=0
            )
        ).annotate(
            total_activity=F('entry_count') + F('exit_count')
        ).values(
            'id', 'name', 'entry_count', 'exit_count', 'total_activity', 'revenue'
        ).order_by('-total_activity')[:limit]

        return list(stations)

    @staticmethod
    def get_ticket_analytics(start_date=None, end_date=None):
        """Get comprehensive ticket analytics"""
        if not start_date:
            start_date = timezone.localtime().date() - datetime.timedelta(days=30)
        if not end_date:
            end_date = timezone.localtime().date()

        # Get ticket sales by type
        ticket_sales = Ticket.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).values('ticket_type').annotate(
            quantity=Count('id'),
            total_amount=Sum('price')
        ).order_by('-quantity')

        # Get subscription sales by type
        subscription_sales = UserSubscription.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).values('plan__type').annotate(
            quantity=Count('id'),
            total_amount=Sum('plan__price')
        ).order_by('-quantity')

        # Daily sales trend
        daily_ticket_sales = Ticket.objects.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            quantity=Count('id'),
            revenue=Sum('price')
        ).order_by('date')

        # Hourly distribution
        hourly_usage = Ticket.objects.filter(
            entry_time__date__gte=start_date,
            entry_time__date__lte=end_date,
            entry_time__isnull=False
        ).annotate(
            hour=ExtractHour('entry_time')
        ).values('hour').annotate(
            entries=Count('id')
        ).order_by('hour')

        hourly_exits = Ticket.objects.filter(
            exit_time__date__gte=start_date,
            exit_time__date__lte=end_date,
            exit_time__isnull=False
        ).annotate(
            hour=ExtractHour('exit_time')
        ).values('hour').annotate(
            exits=Count('id')
        ).order_by('hour')

        # Merge hourly data
        hourly_data = {}
        for entry in hourly_usage:
            hour = entry['hour']
            hourly_data[hour] = {
                'hour': hour,
                'entries': entry['entries'],
                'exits': 0
            }

        for exit in hourly_exits:
            hour = exit['hour']
            if hour not in hourly_data:
                hourly_data[hour] = {
                    'hour': hour,
                    'entries': 0,
                    'exits': exit['exits']
                }
            else:
                hourly_data[hour]['exits'] = exit['exits']

        hourly_results = []
        for hour, data in sorted(hourly_data.items()):
            data['total'] = data['entries'] + data['exits']
            hourly_results.append(data)

        return {
            'ticket_sales': list(ticket_sales),
            'subscription_sales': list(subscription_sales),
            'daily_trend': list(daily_ticket_sales),
            'hourly_usage': hourly_results
        }

    @staticmethod
    def get_station_analytics(start_date=None, end_date=None):
        """Get station performance analytics"""
        if not start_date:
            start_date = timezone.localtime().date() - datetime.timedelta(days=30)
        if not end_date:
            end_date = timezone.localtime().date()

        # Get all stations traffic data
        stations_traffic = Station.objects.annotate(
            entries=Count(
                'ticket_entries',  # Changed from 'entry_tickets'
                filter=Q(
                    ticket_entries__entry_time__date__gte=start_date,  # Changed from entry_tickets
                    ticket_entries__entry_time__date__lte=end_date
                )
            ),
            exits=Count(
                'ticket_exits',  # Changed from 'exit_tickets'
                filter=Q(
                    ticket_exits__exit_time__date__gte=start_date,  # Changed from exit_tickets
                    ticket_exits__exit_time__date__lte=end_date
                )
            ),
            revenue=Sum(
                'ticket_entries__price',  # Changed from 'entry_tickets__price'
                filter=Q(
                    ticket_entries__created_at__date__gte=start_date,  # Changed from entry_tickets
                    ticket_entries__created_at__date__lte=end_date
                ),
                default=0
            )
        ).annotate(
            total_traffic=F('entries') + F('exits')
        ).values(
            'id', 'name', 'entries', 'exits', 'total_traffic', 'revenue'
        )

        # Get popular routes (origin-destination pairs)
        popular_routes = Ticket.objects.filter(
            entry_time__date__gte=start_date,
            entry_time__date__lte=end_date,
            exit_time__date__gte=start_date,
            exit_time__date__lte=end_date,
            entry_station__isnull=False,
            exit_station__isnull=False
        ).exclude(entry_station=F('exit_station')).values(
            'entry_station__name', 'exit_station__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:20]

        # Get station usage by day of week
        day_of_week_usage = Ticket.objects.filter(
            entry_time__date__gte=start_date,
            entry_time__date__lte=end_date,
            entry_station__isnull=False
        ).annotate(
            day_of_week=ExtractWeekDay('entry_time')  # 1=Sunday, 7=Saturday
        ).values('day_of_week').annotate(
            count=Count('id')
        ).order_by('day_of_week')

        # Convert day numbers to names
        days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        day_usage = []
        for entry in day_of_week_usage:
            day_index = entry['day_of_week'] % 7  # Adjust for different DB conventions
            day_usage.append({
                'day': days[day_index],
                'count': entry['count']
            })

        return {
            'stations_traffic': list(stations_traffic),
            'popular_routes': list(popular_routes),
            'day_of_week_usage': day_usage
        }
