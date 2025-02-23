# apps/trains/api/views.py

from venv import logger

from django.core.cache import cache
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework import status as drf_status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Schedule, Train, TrainCar
from ..services.crowd_service import CrowdService
from ..services.train_service import TrainService
from .filters import TrainFilter
from .serializers import CrowdLevelSerializer, ScheduleSerializer, TrainDetailSerializer, TrainSerializer


@extend_schema(tags=["Trains"])
class TrainViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing train operations.
    Provides CRUD operations and additional actions for train management.
    """

    serializer_class = TrainSerializer
    permission_classes = [IsAuthenticated]
    filterset_class = TrainFilter
    search_fields = ["train_id", "line__name"]
    ordering_fields = ["train_id", "status", "last_updated"]
    train_service = TrainService()

    def get_queryset(self):
        """Get optimized queryset with related fields"""
        return (
            Train.objects.all()
            .select_related("line", "current_station", "next_station")
            .prefetch_related(Prefetch("cars", queryset=TrainCar.objects.select_related("train")))
        )

    @extend_schema(
        summary="List all trains",
        parameters=[
            OpenApiParameter(name="line_id", type=str, description="Filter by line ID"),
            OpenApiParameter(name="status", type=str, description="Filter by train status"),
            OpenApiParameter(name="search", type=str, description="Search trains"),
            OpenApiParameter(name="ordering", type=str, description="Order results"),
        ],
    )
    def list(self, request):
        """Get list of trains with filtering, searching, and ordering"""
        try:
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)

            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response({"status": "success", "count": queryset.count(), "data": serializer.data})
        except Exception as e:
            logger.error(f"Error listing trains: {str(e)}")
            return Response(
                {"error": "Failed to retrieve trains"},
                status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(summary="Get train details", responses={200: TrainDetailSerializer})
    def retrieve(self, request, pk=None):
        """Get detailed information about a specific train"""
        try:
            train = self.get_object()
            serializer = TrainDetailSerializer(train)

            # Get cached status
            train_status = self.get_train_status(train.train_id)

            # Get crowd information
            crowd_service = CrowdService()
            crowd_info = crowd_service.get_crowd_levels(train)

            return Response(
                {
                    "status": "success",
                    "data": {
                        **serializer.data,
                        "current_status": train_status,
                        "crowd_info": crowd_info,
                    },
                }
            )
        except Train.DoesNotExist:
            return Response({"error": "Train not found"}, status=drf_status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error retrieving train: {str(e)}")
            return Response(
                {"error": "Failed to retrieve train details"},
                status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_train_status(self, train_id):
        """Get cached train status with automatic refresh"""
        cache_key = f"train_status_{train_id}"
        cached_status = cache.get(cache_key)

        if not cached_status:
            try:
                status = self.train_service.calculate_train_status(train_id)
                cache.set(cache_key, status, timeout=30)
                return status
            except Exception as e:
                logger.error(f"Error calculating train status: {str(e)}")
                return None

        return cached_status

    @extend_schema(
        summary="Get train status",
        parameters=[OpenApiParameter(name="train_id", type=str, required=True)],
    )
    @action(detail=False, methods=["GET"])
    def train_status(self, request):
        """Get current status of a specific train"""
        train_id = request.query_params.get("train_id")
        if not train_id:
            return Response(
                status=drf_status.HTTP_400_BAD_REQUEST,
            )

        try:
            status_data = self.get_train_status(train_id)
            if not status_data:
                return Response(
                    {"error": "Failed to retrieve train status"},
                    status=drf_status.HTTP_404_NOT_FOUND,
                )

            return Response({"status": "success", "data": status_data, "timestamp": timezone.now()})
        except Exception as e:
            logger.error(f"Error getting train status: {str(e)}")
            return Response(
                {"error": "Failed to retrieve train status"},
                status=drf_status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @extend_schema(
        summary="Get trains by line",
        parameters=[OpenApiParameter(name="line_id", type=str, required=True)],
    )
    @action(detail=False, methods=["GET"])
    def line_trains(self, request):
        """Get all trains for a specific line with real-time information"""
        line_id = request.query_params.get("line_id")
        if not line_id:
            return Response({"error": "line_id is required"}, status=drf_status.HTTP_400_BAD_REQUEST)

        try:
            trains = self.get_queryset().filter(line_id=line_id)
            serializer = self.get_serializer(trains, many=True)

            # Enhance with real-time data
            enhanced_data = []
            for train_data in serializer.data:
                train_id = train_data["train_id"]
                status = self.get_train_status(train_id)
                enhanced_data.append({**train_data, "real_time_status": status})

            return Response(
                {
                    "status": "success",
                    "count": len(enhanced_data),
                    "data": enhanced_data,
                    "timestamp": timezone.now(),
                }
            )
        except Exception as e:
            logger.error(f"Error getting line trains: {str(e)}")
            return Response(
                {"error": "Failed to retrieve line trains"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(tags=["Schedules"])
class ScheduleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing train schedules.
    Provides CRUD operations and additional actions for schedule management.
    """

    serializer_class = ScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Schedule.objects.all().select_related("train", "station").order_by("sequence_number")

    @extend_schema(
        summary="Get station schedule",
        parameters=[OpenApiParameter(name="station_id", type=str, required=True)],
    )
    @action(detail=False, methods=["GET"])
    def station_schedule(self, request):
        """Get schedule for a specific station with real-time updates"""
        station_id = request.query_params.get("station_id")
        if not station_id:
            return Response({"error": "station_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            schedules = self.get_queryset().filter(station_id=station_id, is_active=True)
            serializer = self.get_serializer(schedules, many=True)

            return Response(
                {
                    "status": "success",
                    "count": schedules.count(),
                    "data": serializer.data,
                    "timestamp": timezone.now(),
                }
            )
        except Exception as e:
            logger.error(f"Error getting station schedule: {str(e)}")
            return Response(
                {"error": "Failed to retrieve station schedule"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TrainCrowdView(APIView):
    """
    API View for managing train crowd levels.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = CrowdLevelSerializer
    crowd_service = CrowdService()

    @extend_schema(summary="Get crowd levels", responses={200: CrowdLevelSerializer})
    def get(self, request, train_id):
        """Get current crowd levels for a train"""
        try:
            train = get_object_or_404(Train, id=train_id)  # Using integer ID
            crowd_service = CrowdService()

            # Get current crowd data
            crowd_data = crowd_service.get_crowd_levels(train)

            if not crowd_data:
                return Response(
                    {"error": "Failed to retrieve crowd levels"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Format response for Flutter
            response_data = {
                "train_id": int(train_id),
                "crowd_data": [
                    {
                        "car_id": data["car_id"],
                        "crowd_level": data["crowd_level"],
                        "timestamp": data["timestamp"]
                    } for data in crowd_data["crowd_data"]
                ],
                "is_ac": train.has_air_conditioning
            }

            # Cache the response
            cache_key = f"crowd_data_{train_id}"
            cache.set(cache_key, response_data, timeout=30)  # Cache for 30 seconds

            return Response(response_data)

        except Train.DoesNotExist:
            return Response(
                {"error": "Train not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error getting crowd levels: {str(e)}")
            return Response(
                {"error": "Failed to retrieve crowd levels"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(tags=["Trains"])
class TrainListView(APIView):
    """
    API View for custom train listing.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = TrainSerializer

    @extend_schema(summary="List trains with custom format", responses={200: TrainSerializer(many=True)})
    def get(self, request):
        try:
            trains = Train.objects.all().select_related("line", "current_station", "next_station")
            serializer = self.serializer_class(trains, many=True)
            return Response(
                {
                    "status": "success",
                    "count": trains.count(),
                    "data": serializer.data,
                    "timestamp": timezone.now(),
                }
            )
        except Exception as e:
            logger.error(f"Error in custom train list: {str(e)}")
            return Response({"error": "Failed to retrieve trains"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(tags=["Trains"])
class TrainDetailView(APIView):
    """
    API View for custom train details.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = TrainDetailSerializer

    @extend_schema(summary="Get detailed train information", responses={200: TrainDetailSerializer})
    def get(self, request, train_id):
        try:
            train = get_object_or_404(Train, train_id=train_id)
            serializer = self.serializer_class(train)

            # Get additional information
            train_service = TrainService()
            crowd_service = CrowdService()

            return Response(
                {
                    "status": "success",
                    "data": {
                        **serializer.data,
                        "real_time_status": train_service.calculate_train_status(train_id),
                        "crowd_info": crowd_service.get_crowd_levels(train),
                    },
                    "timestamp": timezone.now(),
                }
            )
        except Train.DoesNotExist:
            return Response({"error": "Train not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in custom train detail: {str(e)}")
            return Response(
                {"error": "Failed to retrieve train details"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(tags=["Schedules"])
class TrainScheduleView(APIView):
    """
    API View for retrieving train schedules.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ScheduleSerializer

    @extend_schema(summary="Get train schedule", responses={200: ScheduleSerializer(many=True)})
    def get(self, request, train_id):
        """Get schedule for a specific train"""
        try:
            train = get_object_or_404(Train, train_id=train_id)

            # Get train schedules
            schedules = (
                Schedule.objects.filter(train=train, is_active=True)
                .select_related("station")
                .order_by("sequence_number")
            )

            serializer = self.serializer_class(schedules, many=True)

            # Get real-time updates
            train_service = TrainService()
            current_status = train_service.calculate_train_status(train_id)

            # Calculate estimated arrival times
            schedule_data = []
            for schedule in serializer.data:
                estimated_time = train_service.calculate_estimated_arrival(train_id, schedule["station"])
                schedule_data.append({**schedule, "estimated_arrival": estimated_time})

            return Response(
                {
                    "status": "success",
                    "data": {
                        "schedule": schedule_data,
                        "current_status": current_status,
                        "last_updated": timezone.now(),
                    },
                }
            )
        except Train.DoesNotExist:
            return Response({"error": "Train not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error getting train schedule: {str(e)}")
            return Response(
                {"error": "Failed to retrieve train schedule"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
