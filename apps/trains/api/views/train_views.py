# apps/trains/api/views/train_views.py

from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import get_object_or_404
from django.urls import get_resolver
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from apps.stations.models import Station
from apps.trains.models.schedule import Schedule
from apps.trains.utils.file_validator import FileValidator
from ...services.schedule_service import ScheduleService
from ...services.crowd_service import CrowdDetectionService
from ...models.train import Train
from ..serializers.train_serializer import TrainSerializer, TrainDetailSerializer
from ..serializers.schedule_serializer import ScheduleSerializer
from ..pagination import StandardResultsSetPagination
from ..permissions import IsStaffOrReadOnly, CanUpdateCrowdLevel
from ..filters import TrainFilter
import logging

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class TrainViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing train operations and schedules.

    Provides endpoints for:
    - Train schedules retrieval
    - Crowd level monitoring
    - Train location updates
    - Debug information

    Public Endpoints:
    - GET /api/trains/ - List all trains
    - GET /api/trains/{id}/ - Get train details
    - POST /api/trains/get-schedules/ - Get upcoming schedules
    - GET /api/trains/debug/ - Get API debug info
    - GET /api/trains/{id}/station-schedule/ - Get station schedule

    Protected Endpoints (require authentication):
    - POST /api/trains/{id}/update-crowd-level/ - Update crowd level
    - POST /api/trains/{id}/update-location/ - Update train location
    - POST /api/trains/ - Create new train
    - PUT/PATCH /api/trains/{id}/ - Update train
    - DELETE /api/trains/{id}/ - Delete train
    """

    queryset = (
        Train.objects.all()
        .select_related("line", "current_station", "next_station")
        .prefetch_related("cars")
    )
    serializer_class = TrainSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = TrainFilter
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def get_permissions(self):
        """
        Customize permissions based on action with more granular control
        """
        public_actions = [
            "list",
            "retrieve",
            "get_schedules",
            "debug_info",
            "station_schedule",
        ]
        staff_actions = ["update_crowd_level", "update_location", "create", "destroy"]

        if self.action in public_actions:
            return [AllowAny()]
        elif self.action in staff_actions:
            return [IsAuthenticated(), CanUpdateCrowdLevel()]
        else:
            return [IsAuthenticated(), IsStaffOrReadOnly()]

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action in ["retrieve", "update_crowd_level"]:
            return TrainDetailSerializer
        return TrainSerializer

    @swagger_auto_schema(
        operation_description="Get upcoming train schedules between stations",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "start_station": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Starting station ID"
                ),
                "end_station": openapi.Schema(
                    type=openapi.TYPE_INTEGER, description="Destination station ID"
                ),
            },
            required=["start_station", "end_station"],
        ),
        responses={
            200: ScheduleSerializer(many=True),
            400: "Bad Request",
            404: "Not Found",
            500: "Internal Server Error",
        },
        tags=["Schedules"],
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="get-schedules",
        url_name="get_schedules",
        permission_classes=[AllowAny],
    )
    def get_schedules(self, request):
        """Get upcoming trains and their crowd levels"""
        try:
            start_station_id = request.data.get("start_station")
            end_station_id = request.data.get("end_station")

            if not all([start_station_id, end_station_id]):
                return Response(
                    {"error": "Both start and end stations are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Get stations
            start_station = Station.objects.get(id=start_station_id)
            end_station = Station.objects.get(id=end_station_id)

            # Get upcoming schedules
            now = timezone.now()
            schedules = (
                Schedule.objects.filter(station=start_station, arrival_time__gt=now)
                .select_related("train", "train__line", "station")
                .prefetch_related("train__cars")
                .order_by("arrival_time")[:3]
            )

            # If no upcoming schedules, create some for the next hour
            if not schedules:
                trains = Train.objects.filter(
                    current_station=start_station, status="IN_SERVICE"
                )[:2]

                for idx, train in enumerate(trains):
                    Schedule.objects.create(
                        train=train,
                        station=start_station,
                        arrival_time=now + timezone.timedelta(minutes=15 + idx * 15),
                        departure_time=now + timezone.timedelta(minutes=17 + idx * 15),
                        status="ON_TIME",
                    )

                # Refresh schedules query
                schedules = (
                    Schedule.objects.filter(station=start_station, arrival_time__gt=now)
                    .select_related("train", "train__line", "station")
                    .prefetch_related("train__cars")
                    .order_by("arrival_time")[:3]
                )

            # Format response
            data = {
                "schedules": [
                    {
                        "id": schedule.id,
                        "train_number": schedule.train.train_number,
                        "line": {
                            "name": schedule.train.line.name,
                            "color_code": schedule.train.line.color_code,
                        },
                        "direction": schedule.train.direction,
                        "arrival_time": schedule.arrival_time.isoformat(),
                        "departure_time": schedule.departure_time.isoformat(),
                        "waiting_time": {
                            "minutes": int(
                                (schedule.arrival_time - now).total_seconds() // 60
                            ),
                            "formatted": f"{int((schedule.arrival_time - now).total_seconds() // 60)} mins",
                        },
                        "status": schedule.status,
                        "has_ac": schedule.train.has_ac,
                        "crowd_info": {
                            "level": schedule.train.get_crowd_level(),
                            "monitored_car": self._get_monitored_car_info(
                                schedule.train
                            ),
                        },
                        "stations": {
                            "start": {
                                "id": start_station.id,
                                "name": start_station.name,
                            },
                            "end": {"id": end_station.id, "name": end_station.name},
                        },
                    }
                    for schedule in schedules
                ],
                "meta": {
                    "total_schedules": len(schedules),
                    "timestamp": now.isoformat(),
                    "station_info": {
                        "name": start_station.name,
                        "is_interchange": start_station.is_interchange(),
                        "connecting_lines": [
                            {"name": line.name, "color_code": line.color_code}
                            for line in start_station.lines.all()
                        ],
                    },
                },
            }

            return Response(data)

        except Station.DoesNotExist:
            return Response(
                {"error": "Station not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error getting schedules: {str(e)}")
            return Response(
                {"error": "Failed to retrieve schedules", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _get_monitored_car_info(self, train):
        """Get monitored car information if available"""
        if not train.is_monitored or not train.camera_car_number:
            return None

        try:
            car = train.cars.get(car_number=train.camera_car_number)
            return {
                "car_number": car.car_number,
                "current_passengers": car.current_passengers,
                "crowd_level": car.crowd_level,
            }
        except Exception:
            return None

    @action(detail=True, methods=["get"])
    def station_schedule(self, request, pk=None):
        """Get schedule for a specific station"""
        try:
            time_window = int(request.query_params.get("time_window", 30))
            schedule_service = ScheduleService()
            result = schedule_service.get_station_schedule(pk, time_window)
            return Response(result)
        except ValueError:
            return Response(
                {"error": "Invalid time window value"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Error getting station schedule: {str(e)}")
            return Response(
                {"error": "Failed to retrieve station schedule"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated, CanUpdateCrowdLevel],
        url_path='update-crowd-level'
    )
    def update_crowd_level(self, request, pk=None):
        """
        Comprehensive crowd level update endpoint
        """
        try:
            # Comprehensive logging for debugging
            logger.info("=" * 50)
            logger.info("Crowd Level Update Request Received")
            logger.info(f"Request Method: {request.method}")
            logger.info(f"Content Type: {request.content_type}")
            logger.info(f"Request DATA keys: {list(request.data.keys())}")
            logger.info(f"Request FILES keys: {list(request.FILES.keys()) if request.FILES else 'No files'}")
            logger.info(f"Raw POST data: {request.POST}")

            # Multiple ways to extract car number
            car_number = (
                request.data.get('car_number')
                or request.POST.get('car_number')
                or request.GET.get('car_number')
            )

            # Multiple ways to extract image
            image_input = (
                request.FILES.get('image')
                or request.FILES.get('file')
                or request.data.get('image')
            )

            # Validate car number
            if not car_number:
                return Response(
                    {
                        "error": "Car number is required",
                        "details": {
                            "request_data_keys": list(request.data.keys()),
                            "request_files_keys": list(request.FILES.keys()) if request.FILES else "No files",
                            "suggestion": "Provide car_number in request data"
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate image
            if not image_input:
                return Response(
                    {
                        "error": "Image is required",
                        "details": {
                            "request_data_keys": list(request.data.keys()),
                            "request_files_keys": list(request.FILES.keys()) if request.FILES else "No files",
                            "suggestions": [
                                "Ensure 'image' is the key for file upload",
                                "Verify file is selected",
                                "Check form-data configuration"
                            ]
                        }
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Comprehensive file validation
            file_validator = FileValidator()
            is_valid, validated_file, error_message = file_validator.validate_file(image_input)

            if not is_valid:
                return Response(
                    {
                        "error": "File validation failed",
                        "details": error_message
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Convert car number to integer
            try:
                car_number = int(car_number)
            except ValueError:
                return Response(
                    {
                        "error": "Invalid car number format",
                        "details": "Car number must be an integer"
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Get train and specific car
            train = self.get_object()
            car = get_object_or_404(train.cars, car_number=car_number)

            # Read file content
            image_content = validated_file.read()

            # Log image processing details
            logger.info(f"Processing image for Train {train.train_number}, Car {car.car_number}")
            logger.info(f"Image size: {len(image_content)} bytes")

            # Process image asynchronously
            from asgiref.sync import async_to_sync
            crowd_service = CrowdDetectionService()

            try:
                result = async_to_sync(crowd_service.update_car_crowd_level)(car, image_content)
            except Exception as async_error:
                logger.error(f"Async crowd level update error: {async_error}", exc_info=True)
                return Response(
                    {
                        "error": "Crowd detection process failed",
                        "details": str(async_error),
                        "suggestions": [
                            "Verify AI service availability",
                            "Check network connectivity",
                            "Retry the request",
                            "Contact system administrator"
                        ]
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

            # Close file if it was opened
            if hasattr(validated_file, 'close'):
                validated_file.close()

            # Handle AI service response
            if not result.get('success', False):
                logger.warning(f"Crowd detection failed: {result}")
                return Response(
                    {
                        "error": "Crowd detection failed",
                        "details": result.get('details', 'Unknown error'),
                        "suggestions": result.get('fallback_suggestion', [])
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Successful response
            logger.info("Crowd level update successful")
            return Response(
                {
                    "success": True,
                    "crowd_level": result.get('crowd_level'),
                    "passenger_count": result.get('passenger_count'),
                    "train_number": train.train_number,
                    "car_number": car.car_number
                }
            )

        except Exception as e:
            # Comprehensive error logging
            logger.error(f"Unexpected error in crowd level update: {e}", exc_info=True)
            return Response(
                {
                    'error': 'Comprehensive crowd level update failure',
                    'details': str(e),
                    'suggestions': [
                        "Check system logs",
                        "Verify AI service status",
                        "Retry the request"
                    ]
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @swagger_auto_schema(
        operation_description="Get API debug information",
        responses={
            200: openapi.Response(
                description="Debug information",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "api_status": openapi.Schema(type=openapi.TYPE_STRING),
                        "version": openapi.Schema(type=openapi.TYPE_STRING),
                        "available_actions": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "name": openapi.Schema(type=openapi.TYPE_STRING),
                                    "method": openapi.Schema(type=openapi.TYPE_STRING),
                                    "url": openapi.Schema(type=openapi.TYPE_STRING),
                                    "description": openapi.Schema(
                                        type=openapi.TYPE_STRING
                                    ),
                                    "requires_auth": openapi.Schema(
                                        type=openapi.TYPE_BOOLEAN
                                    ),
                                    "parameters": openapi.Schema(
                                        type=openapi.TYPE_ARRAY,
                                        items=openapi.Schema(type=openapi.TYPE_STRING),
                                    ),
                                },
                            ),
                        ),
                        "registered_urls": openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            additional_properties=openapi.Schema(
                                type=openapi.TYPE_STRING
                            ),
                        ),
                        "authentication_required": openapi.Schema(
                            type=openapi.TYPE_BOOLEAN
                        ),
                        "supported_methods": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(type=openapi.TYPE_STRING),
                        ),
                        "documentation_url": openapi.Schema(type=openapi.TYPE_STRING),
                    },
                ),
            ),
            400: "Bad Request",
            500: "Internal Server Error",
        },
        tags=["Debug"],
    )
    @action(
        detail=False,
        methods=["get"],
        permission_classes=[AllowAny],
        url_path="debug",
        url_name="debug_info",
    )
    def debug_info(self, request) -> Response:
        """Debug endpoint to show API information and available URLs"""
        try:
            # Get all train-related URLs
            urls = get_resolver().reverse_dict
            train_urls = {
                pattern: str(url)
                for pattern, url in urls.items()
                if isinstance(pattern, str) and "train" in pattern
            }

            # Define available actions with metadata
            available_actions = [
                {
                    "name": "get_schedules",
                    "method": "POST",
                    "url": "/api/trains/get-schedules/",
                    "description": "Get upcoming train schedules",
                    "requires_auth": False,
                    "parameters": ["start_station", "end_station"],
                },
                {
                    "name": "update_crowd_level",
                    "method": "POST",
                    "url": "/api/trains/{train_id}/update-crowd-level/",
                    "description": "Update train car crowd level",
                    "requires_auth": True,
                    "parameters": ["car_number", "image"],
                },
                {
                    "name": "station_schedule",
                    "method": "GET",
                    "url": "/api/trains/{train_id}/station-schedule/",
                    "description": "Get schedule for specific station",
                    "requires_auth": False,
                    "parameters": ["time_window"],
                },
            ]

            return Response(
                {
                    "api_status": "operational",
                    "version": "1.0",
                    "registered_urls": train_urls,
                    "available_actions": available_actions,
                    "authentication_required": False,
                    "supported_methods": list(self.http_method_names),
                    "documentation_url": "/api/docs/",
                }
            )
        except Exception as e:
            logger.error(f"Error in debug info: {str(e)}")
            return Response(
                {"error": "Failed to retrieve debug information"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
