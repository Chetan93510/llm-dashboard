"""
LLM Observability Dashboard - DRF Serializers

This module defines serializers for API data validation and transformation.
"""

from rest_framework import serializers
from .models import LLMRequestLog, UserFeedback, AlertRule, AlertLog


class LLMRequestLogSerializer(serializers.ModelSerializer):
    """Serializer for LLM request logs."""
    
    class Meta:
        model = LLMRequestLog
        fields = [
            'request_id',
            'user_id',
            'model_name',
            'prompt_text',
            'response_text',
            'prompt_tokens',
            'completion_tokens',
            'total_tokens',
            'latency_ms',
            'cost_estimate',
            'status',
            'error_type',
            'error_message',
            'timestamp',
            'metadata',
        ]
        read_only_fields = ['request_id', 'timestamp']


class LLMRequestLogListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing logs (excludes large text fields)."""
    
    class Meta:
        model = LLMRequestLog
        fields = [
            'request_id',
            'user_id',
            'model_name',
            'prompt_tokens',
            'completion_tokens',
            'total_tokens',
            'latency_ms',
            'cost_estimate',
            'status',
            'error_type',
            'timestamp',
        ]


class UserFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for user feedback."""
    
    request_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = UserFeedback
        fields = [
            'id',
            'request_id',
            'rating',
            'comment',
            'user_id',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        request_id = validated_data.pop('request_id')
        try:
            request = LLMRequestLog.objects.get(request_id=request_id)
        except LLMRequestLog.DoesNotExist:
            raise serializers.ValidationError({
                'request_id': 'LLM request not found.'
            })
        return UserFeedback.objects.create(request=request, **validated_data)


class UserFeedbackDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer including request info."""
    
    request = LLMRequestLogListSerializer(read_only=True)
    
    class Meta:
        model = UserFeedback
        fields = [
            'id',
            'request',
            'rating',
            'comment',
            'user_id',
            'created_at',
        ]


class AlertRuleSerializer(serializers.ModelSerializer):
    """Serializer for alert rules."""
    
    class Meta:
        model = AlertRule
        fields = [
            'id',
            'name',
            'description',
            'metric_type',
            'threshold',
            'is_active',
            'notify_email',
            'created_at',
            'updated_at',
            'last_triggered_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_triggered_at']


class AlertLogSerializer(serializers.ModelSerializer):
    """Serializer for alert logs."""
    
    alert_rule_name = serializers.CharField(source='alert_rule.name', read_only=True)
    
    class Meta:
        model = AlertLog
        fields = [
            'id',
            'alert_rule',
            'alert_rule_name',
            'message',
            'metric_value',
            'triggered_at',
            'acknowledged',
            'acknowledged_at',
        ]


# ============================================
# Metrics Serializers
# ============================================

class MetricsOverviewSerializer(serializers.Serializer):
    """Serializer for overview metrics."""
    
    total_calls = serializers.IntegerField()
    total_tokens = serializers.IntegerField()
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=4)
    avg_latency_ms = serializers.FloatField()
    p95_latency_ms = serializers.FloatField()
    error_rate = serializers.FloatField()
    success_count = serializers.IntegerField()
    error_count = serializers.IntegerField()


class TokenUsageSerializer(serializers.Serializer):
    """Serializer for token usage over time."""
    
    period = serializers.CharField()
    prompt_tokens = serializers.IntegerField()
    completion_tokens = serializers.IntegerField()
    total_tokens = serializers.IntegerField()
    cost = serializers.DecimalField(max_digits=10, decimal_places=4)


class LatencyMetricsSerializer(serializers.Serializer):
    """Serializer for latency metrics."""
    
    model_name = serializers.CharField()
    avg_latency_ms = serializers.FloatField()
    min_latency_ms = serializers.IntegerField()
    max_latency_ms = serializers.IntegerField()
    p95_latency_ms = serializers.FloatField()
    call_count = serializers.IntegerField()


class ErrorMetricsSerializer(serializers.Serializer):
    """Serializer for error metrics."""
    
    error_type = serializers.CharField()
    count = serializers.IntegerField()
    percentage = serializers.FloatField()


class ModelUsageSerializer(serializers.Serializer):
    """Serializer for model usage breakdown."""
    
    model_name = serializers.CharField()
    call_count = serializers.IntegerField()
    total_tokens = serializers.IntegerField()
    total_cost = serializers.DecimalField(max_digits=10, decimal_places=4)
    percentage = serializers.FloatField()


class FeedbackAnalyticsSerializer(serializers.Serializer):
    """Serializer for feedback analytics."""
    
    total_feedback = serializers.IntegerField()
    thumbs_up_count = serializers.IntegerField()
    thumbs_down_count = serializers.IntegerField()
    thumbs_up_percentage = serializers.FloatField()
    thumbs_down_percentage = serializers.FloatField()


# ============================================
# LLM Service Request/Response Serializers
# ============================================

class LLMPromptRequestSerializer(serializers.Serializer):
    """Serializer for LLM prompt requests."""
    
    prompt = serializers.CharField(required=True)
    model = serializers.CharField(required=False)
    user_id = serializers.CharField(required=False, allow_null=True)
    max_tokens = serializers.IntegerField(required=False, default=1024)
    temperature = serializers.FloatField(required=False, default=0.7)


class LLMPromptResponseSerializer(serializers.Serializer):
    """Serializer for LLM prompt responses."""
    
    request_id = serializers.UUIDField()
    response = serializers.CharField()
    model = serializers.CharField()
    prompt_tokens = serializers.IntegerField()
    completion_tokens = serializers.IntegerField()
    total_tokens = serializers.IntegerField()
    latency_ms = serializers.IntegerField()
    cost_estimate = serializers.DecimalField(max_digits=10, decimal_places=6)
