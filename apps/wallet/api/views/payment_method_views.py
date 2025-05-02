from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ...models.payment_method import PaymentMethod
from ..serializers.payment_method_serializers import (
    PaymentMethodListSerializer,
    PaymentMethodDetailSerializer,
    PaymentMethodCreateSerializer
)


class PaymentMethodViewSet(viewsets.ModelViewSet):
    """ViewSet for payment method operations"""
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PaymentMethod.objects.filter(user=self.request.user, is_active=True)

    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' or self.action == 'partial_update':
            return PaymentMethodCreateSerializer
        elif self.action == 'retrieve':
            return PaymentMethodDetailSerializer
        return PaymentMethodListSerializer

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set payment method as default"""
        payment_method = self.get_object()
        payment_method.is_default = True
        payment_method.save()

        return Response({
            'success': True,
            'message': 'Payment method set as default',
            'data': PaymentMethodDetailSerializer(payment_method).data
        })

    def destroy(self, request, *args, **kwargs):
        """Soft delete payment method"""
        payment_method = self.get_object()

        # Don't delete if it's the only payment method and it's the default
        if payment_method.is_default:
            other_methods = PaymentMethod.objects.filter(
                user=request.user,
                is_active=True
            ).exclude(pk=payment_method.pk).exists()

            if not other_methods:
                return Response({
                    'success': False,
                    'message': 'Cannot delete the only default payment method'
                }, status=status.HTTP_400_BAD_REQUEST)

        # Soft delete
        payment_method.is_active = False
        payment_method.save()

        return Response({
            'success': True,
            'message': 'Payment method removed'
        })
