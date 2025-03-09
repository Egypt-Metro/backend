# apps/trains/api/views/train_views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from ...services.train_service import TrainService
from ...services.schedule_service import ScheduleService
from ...services.crowd_service import CrowdDetectionService
from ...models.train import Train
from ..serializers.train_serializer import TrainSerializer, TrainDetailSerializer
from ..serializers.schedule_serializer import ScheduleSerializer
from ..pagination import StandardResultsSetPagination
from ..permissions import IsStaffOrReadOnly, CanUpdateCrowdLevel
from ..filters import TrainFilter
from ...utils.error_handling import api_error_handler
import logging

logger = logging.getLogger(__name__)


class TrainViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing train operations
    """
    queryset = Train.objects.all()
    serializer_class = TrainSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [IsAuthenticated, IsStaffOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = TrainFilter

    def get_serializer_class(self):
        if self.action in ['retrieve', 'update_crowd_level']:
            return TrainDetailSerializer
        return TrainSerializer

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'start_station': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID of the starting station"
                ),
                'end_station': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="ID of the destination station"
                ),
            },
            required=['start_station', 'end_station']
        ),
        responses={
            200: ScheduleSerializer(many=True),
            400: 'Bad Request',
            404: 'Not Found'
        }
    )
    @api_error_handler
    @action(detail=False, methods=['post'])
    async def get_schedules(self, request):
        """Get upcoming trains and their crowd levels"""
        start_station_id = request.data.get('start_station')
        end_station_id = request.data.get('end_station')

        if not all([start_station_id, end_station_id]):
            return Response(
                {'error': 'Both start and end stations are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        schedule_service = ScheduleService()
        schedules = await schedule_service.get_upcoming_schedules(
            start_station_id,
            end_station_id,
            limit=3
        )

        serializer = ScheduleSerializer(schedules, many=True)
        return Response(serializer.data)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'time_window',
                openapi.IN_QUERY,
                description="Time window in minutes",
                type=openapi.TYPE_INTEGER,
                default=30
            )
        ],
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'upcoming_arrivals': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_OBJECT)
                        )
                    }
                )
            ),
            404: 'Station not found'
        }
    )
    @api_error_handler
    @action(detail=True, methods=['get'])
    async def station_schedule(self, request, pk=None):
        """Get schedule for a specific station"""
        time_window = int(request.query_params.get('time_window', 30))

        schedule_service = ScheduleService()
        result = await schedule_service.get_station_schedule(pk, time_window)

        return Response(result)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'car_number': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Car number to update"
                ),
                'image': openapi.Schema(
                    type=openapi.TYPE_FILE,
                    description="Image file for crowd detection"
                ),
            },
            required=['car_number', 'image']
        ),
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'crowd_level': openapi.Schema(type=openapi.TYPE_STRING),
                        'passenger_count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    }
                )
            ),
            400: 'Bad Request',
            404: 'Not Found'
        }
    )
    @api_error_handler
    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated, CanUpdateCrowdLevel]
    )
    async def update_crowd_level(self, request, pk=None):
        """Update crowd level for a specific train car"""
        train = self.get_object()
        car_number = request.data.get('car_number')

        if not request.FILES.get('image'):
            return Response(
                {"error": "Image file is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not car_number:
            return Response(
                {"error": "Car number is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not train.is_monitored or train.camera_car_number != int(car_number):
            return Response(
                {"error": "Invalid car number for monitoring"},
                status=status.HTTP_400_BAD_REQUEST
            )

        car = get_object_or_404(train.cars, car_number=car_number)
        service = CrowdDetectionService()
        result = await service.update_car_crowd_level(car, request.FILES['image'].read())

        if "error" in result:
            return Response(result, status=status.HTTP_400_BAD_REQUEST)

        return Response(result)

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'station_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Current station ID"
                ),
                'next_station_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Next station ID (optional)"
                ),
            },
            required=['station_id']
        ),
        responses={
            200: openapi.Response(
                description="Success",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'status': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            ),
            404: 'Not Found'
        }
    )
    @api_error_handler
    @action(detail=True, methods=['post'])
    async def update_location(self, request, pk=None):
        """Update train location"""
        station_id = request.data.get('station_id')
        next_station_id = request.data.get('next_station_id')

        train_service = TrainService()
        await train_service.update_train_location(pk, station_id, next_station_id)

        return Response({'status': 'success'})
