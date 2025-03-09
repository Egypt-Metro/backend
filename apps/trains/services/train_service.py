# apps/trains/services/train_service.py

from typing import Any, List, Dict, Optional
from django.db.models import Q
from datetime import datetime, timedelta
from ..models.train import Train
from ..utils.error_handling import APIError


class TrainService:
    @staticmethod
    async def get_train_details(train_id: int) -> Dict[str, Any]:
        """
        Get detailed information about a train

        Args:
            train_id: The ID of the train

        Returns:
            Dict containing train details, cars, and current schedule

        Raises:
            APIError: If train is not found
        """
        try:
            train = await Train.objects.aget(id=train_id)
            return {
                'train': train,
                'cars': await train.cars.all(),
                'current_schedule': await train.schedules.filter(
                    arrival_time__lte=datetime.now(),
                    departure_time__gte=datetime.now()
                ).afirst()
            }
        except Train.DoesNotExist:
            raise APIError("Train not found", 404)

    @staticmethod
    async def get_trains_by_station(
        station_id: int,
        direction: Optional[str] = None
    ) -> List[Train]:
        """
        Get trains currently at or approaching a station

        Args:
            station_id: The ID of the station
            direction: Optional direction filter

        Returns:
            List of Train objects
        """
        now = datetime.now()
        query = Q(current_station_id=station_id) | Q(
            schedules__station_id=station_id,
            schedules__arrival_time__gte=now,
            schedules__arrival_time__lte=now + timedelta(minutes=30)
        )

        if direction:
            query &= Q(direction=direction)

        return await Train.objects.filter(query).distinct()

    @staticmethod
    async def update_train_location(
        train_id: int,
        station_id: int,
        next_station_id: Optional[int] = None
    ) -> None:
        """
        Update train's current and next station

        Args:
            train_id: The ID of the train
            station_id: The ID of the current station
            next_station_id: Optional ID of the next station

        Raises:
            APIError: If train is not found
        """
        try:
            train = await Train.objects.aget(id=train_id)
            train.current_station_id = station_id
            train.next_station_id = next_station_id
            await train.asave()
        except Train.DoesNotExist:
            raise APIError("Train not found", 404)
