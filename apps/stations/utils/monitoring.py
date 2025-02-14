# apps/stations/utils/monitoring.py
import logging
from django.db.models import Count
from ..models import Line, Station, LineStation

logger = logging.getLogger(__name__)


def monitor_system_status():
    """Monitor the metro system status"""
    try:
        # Check line status
        for line in Line.objects.all():
            station_count = line.stations.count()
            logger.info(f"{line.name}: {station_count} stations")

            # Check for disconnected stations
            disconnected = LineStation.objects.filter(
                line=line
            ).order_by('order').values_list('order', flat=True)

            gaps = []
            for i in range(len(disconnected) - 1):
                if disconnected[i + 1] - disconnected[i] > 1:
                    gaps.append((disconnected[i], disconnected[i + 1]))

            if gaps:
                logger.warning(f"{line.name} has gaps in station order: {gaps}")

        # Check interchange stations
        interchanges = Station.objects.annotate(
            line_count=Count('lines')
        ).filter(line_count__gt=1)

        logger.info(f"Interchange stations: {interchanges.count()}")
        for station in interchanges:
            logger.info(f"{station.name}: connects {', '.join(line.name for line in station.lines.all())}")

    except Exception as e:
        logger.error(f"Error monitoring system status: {e}")
