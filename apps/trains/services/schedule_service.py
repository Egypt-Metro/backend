# apps/trains/services/schedule_service.py

from typing import List, Dict
from datetime import datetime, timedelta
from ..models.schedule import Schedule
from ..utils.error_handling import APIError
from apps.stations.models import Station


class ScheduleService:
    @staticmethod
    async def get_upcoming_schedules(
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
            start_station = await Station.objects.aget(id=start_station_id)
            end_station = await Station.objects.aget(id=end_station_id)

            start_order = await start_station.get_station_order(start_station.lines.first())
            end_order = await end_station.get_station_order(end_station.lines.first())

            direction = "HELWAN" if start_order > end_order else "MARG"

            return await Schedule.objects.filter(
                station=start_station,
                train__direction=direction,
                arrival_time__gt=datetime.now()
            ).select_related(
                'train',
                'station'
            ).order_by(
                'arrival_time'
            )[:limit]

        except Station.DoesNotExist:
            raise APIError("Station not found", 404)
        except Exception as e:
            raise APIError(f"Error getting schedules: {str(e)}")

    @staticmethod
    async def get_station_schedule(
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
        """
        now = datetime.now()
        window_end = now + timedelta(minutes=time_window)

        schedules = await Schedule.objects.filter(
            station_id=station_id,
            arrival_time__range=(now, window_end)
        ).select_related('train').order_by('arrival_time')

        return {
            'upcoming_arrivals': [
                {
                    'train_number': schedule.train.train_number,
                    'arrival_time': schedule.arrival_time,
                    'direction': schedule.train.direction,
                    'crowd_level': schedule.train.get_crowd_level(),
                    'status': schedule.status
                }
                for schedule in schedules
            ]
        }

    @staticmethod
    async def update_schedule_status(schedule_id: int, status: str) -> None:
        """
        Update schedule status

        Args:
            schedule_id: The ID of the schedule
            status: New status value

        Raises:
            APIError: If schedule not found
        """
        try:
            schedule = await Schedule.objects.aget(id=schedule_id)
            schedule.status = status
            await schedule.asave()
        except Schedule.DoesNotExist:
            raise APIError("Schedule not found", 404)
