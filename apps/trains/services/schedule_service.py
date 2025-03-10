# apps/trains/services/schedule_service.py

from typing import List, Dict, Optional
from django.utils import timezone
from datetime import timedelta
from ..models.schedule import Schedule
from apps.stations.models import Station
from ..utils.error_handling import APIError
import logging

logger = logging.getLogger(__name__)


class ScheduleService:
    def get_upcoming_schedules(
        self,
        start_station_id: int,
        end_station_id: int,
        limit: int = 3
    ) -> List[Schedule]:
        """
        Get upcoming train schedules between stations

        Args:
            start_station_id: Starting station ID
            end_station_id: Ending station ID
            limit: Maximum number of schedules to return

        Returns:
            List of Schedule objects

        Raises:
            APIError: If stations not found or other errors occur
        """
        try:
            # Get stations
            start_station = Station.objects.get(id=start_station_id)
            end_station = Station.objects.get(id=end_station_id)

            # Get common lines between stations
            common_lines = set(start_station.lines.all()) & set(end_station.lines.all())
            if not common_lines:
                raise APIError("No direct line between these stations", 404)

            line = common_lines.pop()  # Get first common line

            # Get station orders
            start_order = start_station.get_station_order(line)
            end_order = end_station.get_station_order(line)

            if start_order is None or end_order is None:
                raise APIError("Invalid station configuration", 400)

            # Determine direction based on station orders
            direction = "HELWAN" if start_order > end_order else "MARG"

            # Get upcoming schedules
            now = timezone.now()
            schedules = Schedule.objects.filter(
                station=start_station,
                train__direction=direction,
                train__line=line,
                arrival_time__gt=now
            ).select_related(
                'train',
                'station',
                'train__line'
            ).prefetch_related(
                'train__cars'
            ).order_by(
                'arrival_time'
            )[:limit]

            if not schedules:
                logger.info(
                    f"No schedules found between stations {start_station.name} "
                    f"and {end_station.name}"
                )

            return schedules

        except Station.DoesNotExist:
            logger.error(f"Station not found: {start_station_id} or {end_station_id}")
            raise APIError("Station not found", 404)
        except Exception as e:
            logger.error(f"Error in get_upcoming_schedules: {str(e)}")
            raise APIError(f"Error getting schedules: {str(e)}")

    def get_station_schedule(
        self,
        station_id: int,
        time_window: int = 30
    ) -> Dict[str, List[Dict]]:
        """
        Get all trains arriving at a station within time window

        Args:
            station_id: The ID of the station
            time_window: Time window in minutes

        Returns:
            Dict containing upcoming arrivals

        Raises:
            APIError: If station not found or other errors occur
        """
        try:
            station = Station.objects.get(id=station_id)
            now = timezone.now()
            window_end = now + timedelta(minutes=time_window)

            schedules = Schedule.objects.filter(
                station=station,
                arrival_time__range=(now, window_end)
            ).select_related(
                'train',
                'train__line'
            ).order_by('arrival_time')

            return {
                'station_name': station.name,
                'is_interchange': station.is_interchange(),
                'connecting_lines': [
                    {'name': line.name, 'color_code': line.color_code}
                    for line in station.get_connecting_lines()
                ],
                'upcoming_arrivals': [
                    {
                        'train_number': schedule.train.train_number,
                        'line': {
                            'name': schedule.train.line.name,
                            'color_code': schedule.train.line.color_code
                        },
                        'arrival_time': schedule.arrival_time,
                        'departure_time': schedule.departure_time,
                        'direction': schedule.train.direction,
                        'crowd_level': schedule.train.get_crowd_level(),
                        'status': schedule.status,
                        'has_ac': schedule.train.has_ac,
                        'next_station': self._get_next_station_info(schedule)
                    }
                    for schedule in schedules
                ]
            }

        except Station.DoesNotExist:
            logger.error(f"Station not found: {station_id}")
            raise APIError("Station not found", 404)
        except Exception as e:
            logger.error(f"Error in get_station_schedule: {str(e)}")
            raise APIError(f"Error getting station schedule: {str(e)}")

    def _get_next_station_info(self, schedule: Schedule) -> Optional[Dict]:
        """Helper method to get next station information"""
        try:
            next_station = schedule.station.get_next_station(
                schedule.train.line,
                schedule.train.direction
            )
            if next_station:
                return {
                    'name': next_station.name,
                    'estimated_arrival': schedule.departure_time + timedelta(
                        minutes=schedule.station.get_estimated_time_to(
                            next_station,
                            schedule.train.line
                        )
                    )
                }
            return None
        except Exception as e:
            logger.warning(f"Error getting next station info: {str(e)}")
            return None
