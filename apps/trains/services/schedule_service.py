from datetime import datetime, date
from typing import Optional
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import QuerySet

from ..models.schedule import Schedule, ActualSchedule


class ScheduleService:
    """Service class for managing train schedules and timing."""

    def get_train_schedule(self, train_id: str, schedule_date: date) -> QuerySet[Schedule]:
        """
        Get schedule for specific train and date.

        Args:
            train_id (str): Train identifier
            schedule_date (date): Date for schedule

        Returns:
            QuerySet[Schedule]: Ordered schedule entries
        """
        day_type = self._get_day_type(schedule_date)
        return Schedule.objects.filter(
            train_id=train_id,
            day_type=day_type,
            is_active=True
        ).select_related(
            'station'
        ).order_by('sequence_number')

    def get_station_schedule(
        self,
        station_id: int,
        schedule_date: date
    ) -> QuerySet[Schedule]:
        """
        Get schedule for specific station and date.

        Args:
            station_id (int): Station identifier
            schedule_date (date): Date for schedule

        Returns:
            QuerySet[Schedule]: Ordered schedule entries
        """
        day_type = self._get_day_type(schedule_date)
        return Schedule.objects.filter(
            station_id=station_id,
            day_type=day_type,
            is_active=True
        ).select_related(
            'train'
        ).order_by('arrival_time')

    def record_actual_arrival(
        self,
        schedule_id: int,
        arrival_time: datetime,
        reason: Optional[str] = None
    ) -> ActualSchedule:
        """
        Record actual arrival time and calculate delay.

        Args:
            schedule_id (int): Schedule identifier
            arrival_time (datetime): Actual arrival time
            reason (Optional[str]): Reason for delay if any

        Returns:
            ActualSchedule: Created actual schedule record

        Raises:
            ValidationError: If arrival time is invalid
        """
        try:
            schedule = Schedule.objects.get(id=schedule_id)

            if arrival_time < timezone.now() - timezone.timedelta(hours=1):
                raise ValidationError("Arrival time cannot be more than 1 hour in the past")

            actual = ActualSchedule.objects.create(
                schedule=schedule,
                actual_arrival=arrival_time,
                reason=reason
            )

            self._calculate_delay(actual)
            return actual

        except Schedule.DoesNotExist:
            raise ValidationError(f"Schedule with ID {schedule_id} not found")

    def _get_day_type(self, schedule_date: date) -> str:
        """
        Determine day type (weekday, weekend, holiday).

        Args:
            schedule_date (date): Date to check

        Returns:
            str: Day type identifier
        """
        if self._is_holiday(schedule_date):
            return 'HOLIDAY'

        weekday = schedule_date.weekday()
        if weekday == 5:
            return 'SATURDAY'
        if weekday == 6:
            return 'SUNDAY'
        return 'WEEKDAY'

    def _calculate_delay(self, actual_schedule: ActualSchedule) -> None:
        """
        Calculate delay in minutes and update status.

        Args:
            actual_schedule (ActualSchedule): Actual schedule record
        """
        scheduled_time = datetime.combine(
            actual_schedule.actual_arrival.date(),
            actual_schedule.schedule.arrival_time
        )
        scheduled_time = timezone.make_aware(scheduled_time)

        delay = actual_schedule.actual_arrival - scheduled_time
        delay_minutes = delay.total_seconds() / 60

        actual_schedule.delay_minutes = max(0, delay_minutes)
        actual_schedule.status = self._get_delay_status(delay_minutes)
        actual_schedule.save(update_fields=['delay_minutes', 'status'])

    def _get_delay_status(self, delay_minutes: float) -> str:
        """
        Determine delay status based on minutes.

        Args:
            delay_minutes (float): Delay in minutes

        Returns:
            str: Delay status
        """
        if delay_minutes <= 2:
            return 'ON_TIME'
        if delay_minutes <= 5:
            return 'SLIGHT_DELAY'
        if delay_minutes <= 15:
            return 'DELAYED'
        return 'SIGNIFICANTLY_DELAYED'

    def _is_holiday(self, check_date: date) -> bool:
        """
        Check if date is a holiday.

        Args:
            check_date (date): Date to check

        Returns:
            bool: True if holiday
        """
        # Implement holiday checking logic here
        return False
