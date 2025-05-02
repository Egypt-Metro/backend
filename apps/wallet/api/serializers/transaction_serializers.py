from rest_framework import serializers
from ...models.transaction import Transaction


class TransactionListSerializer(serializers.ModelSerializer):
    """Serializer for listing transactions"""
    payment_method_name = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            'id', 'amount', 'type', 'status',
            'payment_method_name', 'reference_number',
            'description', 'created_at'
        ]

    def get_payment_method_name(self, obj):
        if obj.payment_method:
            return str(obj.payment_method)
        return None


class TransactionDetailSerializer(serializers.ModelSerializer):
    """Serializer for transaction details"""
    payment_method_name = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            'id', 'amount', 'type', 'status',
            'payment_method_name', 'reference_number',
            'related_object_type', 'related_object_id',
            'description', 'created_at', 'updated_at'
        ]

    def get_payment_method_name(self, obj):
        if obj.payment_method:
            return str(obj.payment_method)
        return None


class TransactionFilterSerializer(serializers.Serializer):
    """Serializer for filtering transactions"""
    type = serializers.ChoiceField(choices=Transaction.TRANSACTION_TYPES, required=False)
    status = serializers.ChoiceField(choices=Transaction.TRANSACTION_STATUS, required=False)
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    limit = serializers.IntegerField(min_value=1, max_value=100, required=False)
