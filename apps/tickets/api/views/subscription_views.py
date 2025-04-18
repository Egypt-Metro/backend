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
    SubscriptionValidationSerializer
)
from ...models.subscription import Subscription
from ...services.subscription_service import SubscriptionService


class SubscriptionViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    subscription_service = SubscriptionService()
    http_method_names = ['get', 'post', 'patch']  # Restrict to these methods

    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return SubscriptionListSerializer
        elif self.action == 'create':
            return SubscriptionCreateSerializer
        elif self.action == 'validate_station':
            return SubscriptionValidationSerializer
        return SubscriptionDetailSerializer

    def get_queryset(self):
        """Filter subscriptions by user and optional active status"""
        queryset = Subscription.objects.filter(user=self.request.user)

        if self.action == 'list':
            is_active = self.request.query_params.get('active')
            if is_active is not None:
                is_active = is_active.lower() == 'true'
                if is_active:
                    queryset = queryset.filter(
                        is_active=True,
                        end_date__gte=timezone.now().date()
                    )
                else:
                    queryset = queryset.filter(
                        is_active=False
                    )

        return queryset.select_related('user')

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create a new subscription"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            subscription = self.subscription_service.create_subscription(
                user=request.user,
                subscription_type=serializer.validated_data['subscription_type'],
                zones_count=serializer.validated_data['zones_count'],
                payment_confirmed=serializer.validated_data['payment_confirmation']
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
            is_active=True,
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

        subscription.is_active = False
        subscription.save(update_fields=['is_active', 'updated_at'])

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
