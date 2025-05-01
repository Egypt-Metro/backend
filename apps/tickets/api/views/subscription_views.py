# apps/tickets/api/views/subscription_views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db import transaction
from ..serializers.subscription_serializers import (
    SubscriptionListSerializer,
    SubscriptionDetailSerializer,
    SubscriptionCreateSerializer,
    SubscriptionRecommendationSerializer,
    SubscriptionValidationSerializer
)
from ...models.subscription import UserSubscription
from ...services.subscription_service import SubscriptionService
from ...services.subscription_qr_service import SubscriptionQRService


class SubscriptionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    subscription_service = SubscriptionService()
    qr_service = SubscriptionQRService()
    http_method_names = ['get', 'post', 'patch']

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return SubscriptionListSerializer
        elif self.action == 'create':
            return SubscriptionCreateSerializer
        elif self.action == 'validate_station':
            return SubscriptionValidationSerializer
        elif self.action == 'recommend':
            return SubscriptionRecommendationSerializer
        return SubscriptionDetailSerializer

    def get_queryset(self):
        """Filter subscriptions by user and optional active status"""
        queryset = UserSubscription.objects.filter(user=self.request.user)

        if self.action == 'list':
            is_active = self.request.query_params.get('active')
            if is_active is not None:
                is_active = is_active.lower() == 'true'
                if is_active:
                    queryset = queryset.filter(
                        status='ACTIVE',
                        end_date__gte=timezone.now().date()
                    )
                else:
                    queryset = queryset.filter(
                        status__in=['EXPIRED', 'CANCELLED']
                    )

        return queryset.select_related('user', 'plan')

    @action(detail=False, methods=['get'])
    def recommend(self, request):
        """Get subscription recommendations for a journey"""
        serializer = SubscriptionRecommendationSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        start_station_id = serializer.validated_data['start_station_id']
        end_station_id = serializer.validated_data['end_station_id']

        try:
            recommendations = self.subscription_service.recommend_subscription(
                start_station_id=start_station_id,
                end_station_id=end_station_id
            )

            if 'error' in recommendations:
                return Response(
                    recommendations,
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(recommendations)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create a new subscription"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Updated to pass the optional station IDs when provided
            start_station_id = serializer.validated_data.get('start_station_id')
            end_station_id = serializer.validated_data.get('end_station_id')

            subscription = self.subscription_service.create_subscription(
                user=request.user,
                subscription_type=serializer.validated_data['subscription_type'],
                zones_count=serializer.validated_data['zones_count'],
                payment_confirmed=serializer.validated_data['payment_confirmation'],
                start_station_id=start_station_id,
                end_station_id=end_station_id
            )

            response_serializer = SubscriptionDetailSerializer(subscription)
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get user's current active subscription"""
        active_sub = self.get_queryset().filter(
            status='ACTIVE',
            end_date__gte=timezone.now().date()
        ).first()

        if not active_sub:
            return Response(
                {
                    'message': 'No active subscription found',
                    'current_time': timezone.now()
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = SubscriptionDetailSerializer(active_sub)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def validate_station(self, request, pk=None):
        """Validate if subscription covers a specific station"""
        subscription = self.get_object()
        serializer = SubscriptionValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not subscription.is_active:
            return Response(
                {'error': 'Subscription is not active'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = self.subscription_service.validate_subscription(
            user=request.user,
            station_name=serializer.validated_data['station_name']
        )

        return Response(result)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an active subscription"""
        subscription = self.get_object()

        if not subscription.is_active:
            return Response(
                {'error': 'Subscription is already inactive'},
                status=status.HTTP_400_BAD_REQUEST
            )

        subscription.status = 'CANCELLED'
        subscription.save(update_fields=['status', 'updated_at'])

        return Response(
            SubscriptionDetailSerializer(subscription).data,
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        """Prevent subscription deletion"""
        return Response(
            {
                'error': 'Subscriptions cannot be deleted. Use cancel endpoint instead.',
                'cancel_endpoint': f'/api/subscriptions/{kwargs.get("pk")}/cancel/'
            },
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(detail=True, methods=['get'])
    def qr_code(self, request, pk=None):
        """Generate QR code for a subscription"""
        subscription = self.get_object()

        if not subscription.is_active:
            return Response(
                {'error': 'Cannot generate QR code for inactive subscription'},
                status=status.HTTP_400_BAD_REQUEST
            )

        qr_service = SubscriptionQRService(current_user=request.user)
        qr_data = qr_service.create_subscription_qr_data(subscription)

        try:
            qr_code_base64, validation_hash = qr_service.generate_subscription_qr(qr_data)

            # Optionally store the hash in the database for later verification
            # subscription.qr_validation_hash = validation_hash
            # subscription.save(update_fields=['qr_validation_hash'])

            return Response({
                'qr_code': qr_code_base64,
                'qr_image_url': qr_service.get_qr_image_url(qr_code_base64),
                'subscription_id': subscription.id
            })

        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
