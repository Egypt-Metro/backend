# apps/dashboard/api/serializers.py

from rest_framework import serializers
from ..models import AdminMetrics, SystemAlert, ReportGeneration


class AdminMetricsSerializer(serializers.ModelSerializer):
    """
    Comprehensive serializer for admin metrics
    """
    class Meta:
        model = AdminMetrics
        fields = '__all__'
        read_only_fields = ('created_at',)

    def validate_total_passengers(self, value):
        """
        Additional validation for total passengers
        """
        if value < 0:
            raise serializers.ValidationError(
                "Total passengers cannot be negative"
            )
        return value


class SystemAlertSerializer(serializers.ModelSerializer):
    """
    Advanced system alert serialization
    """
    class Meta:
        model = SystemAlert
        fields = '__all__'
        read_only_fields = (
            'created_at', 'resolved_at',
            'created_by', 'resolved_by'
        )


class ReportGenerationSerializer(serializers.ModelSerializer):
    """
    Report generation serializer
    """
    class Meta:
        model = ReportGeneration
        fields = '__all__'
        read_only_fields = ('generated_at', 'file_path')
