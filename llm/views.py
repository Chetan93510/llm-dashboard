"""
LLM Observability Dashboard - API Views

This module provides REST API endpoints for the LLM observability dashboard.
"""

import csv
import json
from datetime import datetime, timedelta
from io import StringIO

from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from rest_framework import status, viewsets
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from .models import LLMRequestLog, UserFeedback, AlertRule, AlertLog
from .serializers import (
    LLMRequestLogSerializer,
    LLMRequestLogListSerializer,
    UserFeedbackSerializer,
    UserFeedbackDetailSerializer,
    AlertRuleSerializer,
    AlertLogSerializer,
    MetricsOverviewSerializer,
    TokenUsageSerializer,
    LatencyMetricsSerializer,
    ErrorMetricsSerializer,
    ModelUsageSerializer,
    FeedbackAnalyticsSerializer,
    LLMPromptRequestSerializer,
    LLMPromptResponseSerializer,
)
from .metrics import metrics_service
from .services import groq_service, GroqAPIError


# ============================================
# Pagination Classes
# ============================================

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


# ============================================
# Helper Functions
# ============================================

def parse_date_params(request):
    """Parse date range parameters from request."""
    start_date = request.query_params.get('start_date')
    end_date = request.query_params.get('end_date')
    
    if start_date:
        start_date = parse_datetime(start_date)
        if not start_date:
            try:
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except:
                start_date = None
    
    if end_date:
        end_date = parse_datetime(end_date)
        if not end_date:
            try:
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except:
                end_date = None
    
    return start_date, end_date


# ============================================
# LLM Prompt Endpoint
# ============================================

class LLMPromptView(APIView):
    """
    API endpoint to send prompts to the LLM.
    
    POST /api/llm/prompt/
    """
    
    def post(self, request):
        """Send a prompt to the LLM."""
        serializer = LLMPromptRequestSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get user_id from logged-in user
        user_id = getattr(request, 'user_id', None)
        
        try:
            result = groq_service.complete(
                prompt=serializer.validated_data['prompt'],
                model=serializer.validated_data.get('model'),
                user_id=user_id,  # Use logged-in user's ID
                max_tokens=serializer.validated_data.get('max_tokens', 1024),
                temperature=serializer.validated_data.get('temperature', 0.7),
            )
            
            response_serializer = LLMPromptResponseSerializer(result)
            return Response(response_serializer.data)
            
        except GroqAPIError as e:
            return Response(
                {
                    'error': e.message,
                    'error_type': e.error_type,
                },
                status=status.HTTP_502_BAD_GATEWAY
            )


# ============================================
# Metrics Endpoints
# ============================================

class MetricsOverviewView(APIView):
    """
    API endpoint for overview metrics.
    
    GET /api/metrics/overview/
    """
    
    def get(self, request):
        start_date, end_date = parse_date_params(request)
        model = request.query_params.get('model')
        user_id = getattr(request, 'user_id', None)
        
        metrics = metrics_service.get_overview_metrics(
            start_date=start_date,
            end_date=end_date,
            model=model,
            user_id=user_id
        )
        
        serializer = MetricsOverviewSerializer(metrics)
        return Response(serializer.data)


class TokenUsageView(APIView):
    """
    API endpoint for token usage over time.
    
    GET /api/metrics/token-usage/
    """
    
    def get(self, request):
        start_date, end_date = parse_date_params(request)
        model = request.query_params.get('model')
        group_by = request.query_params.get('group_by', 'day')
        user_id = getattr(request, 'user_id', None)
        
        if group_by not in ['hour', 'day', 'month']:
            group_by = 'day'
        
        data = metrics_service.get_token_usage_over_time(
            start_date=start_date,
            end_date=end_date,
            model=model,
            group_by=group_by,
            user_id=user_id
        )
        
        serializer = TokenUsageSerializer(data, many=True)
        return Response(serializer.data)


class LatencyMetricsView(APIView):
    """
    API endpoint for latency metrics.
    
    GET /api/metrics/latency/
    """
    
    def get(self, request):
        start_date, end_date = parse_date_params(request)
        user_id = getattr(request, 'user_id', None)
        
        data = metrics_service.get_latency_metrics(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id
        )
        
        serializer = LatencyMetricsSerializer(data, many=True)
        return Response(serializer.data)


class ErrorMetricsView(APIView):
    """
    API endpoint for error metrics.
    
    GET /api/metrics/errors/
    """
    
    def get(self, request):
        start_date, end_date = parse_date_params(request)
        model = request.query_params.get('model')
        user_id = getattr(request, 'user_id', None)
        
        data = metrics_service.get_error_metrics(
            start_date=start_date,
            end_date=end_date,
            model=model,
            user_id=user_id
        )
        
        serializer = ErrorMetricsSerializer(data, many=True)
        return Response(serializer.data)


class ModelUsageView(APIView):
    """
    API endpoint for model usage breakdown.
    
    GET /api/metrics/model-usage/
    """
    
    def get(self, request):
        start_date, end_date = parse_date_params(request)
        user_id = getattr(request, 'user_id', None)
        
        data = metrics_service.get_model_usage(
            start_date=start_date,
            end_date=end_date,
            user_id=user_id
        )
        
        serializer = ModelUsageSerializer(data, many=True)
        return Response(serializer.data)


class DailyStatsView(APIView):
    """
    API endpoint for daily statistics.
    
    GET /api/metrics/daily-stats/
    """
    
    def get(self, request):
        days = request.query_params.get('days', 7)
        try:
            days = int(days)
        except ValueError:
            days = 7
        
        user_id = getattr(request, 'user_id', None)
        data = metrics_service.get_daily_stats(days=days, user_id=user_id)
        return Response(data)


# ============================================
# Logs Endpoints
# ============================================

class LogsListView(APIView):
    """
    API endpoint for listing LLM request logs.
    
    GET /api/logs/
    """
    pagination_class = StandardResultsSetPagination
    
    def get(self, request):
        start_date, end_date = parse_date_params(request)
        model = request.query_params.get('model')
        status_filter = request.query_params.get('status')
        request_id = request.query_params.get('request_id')
        
        # CRITICAL: Filter by logged-in user only
        queryset = LLMRequestLog.objects.all()
        if hasattr(request, 'user_id') and request.user_id:
            queryset = queryset.filter(user_id=request.user_id)
        
        # Apply other filters
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        if model:
            queryset = queryset.filter(model_name=model)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if request_id:
            queryset = queryset.filter(request_id=request_id)
        
        # Paginate
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = LLMRequestLogListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = LLMRequestLogListSerializer(queryset[:100], many=True)
        return Response(serializer.data)


class LogDetailView(APIView):
    """
    API endpoint for retrieving a single log entry.
    
    GET /api/logs/<request_id>/
    """
    
    def get(self, request, request_id):
        try:
            log = LLMRequestLog.objects.get(request_id=request_id)
            serializer = LLMRequestLogSerializer(log)
            return Response(serializer.data)
        except LLMRequestLog.DoesNotExist:
            return Response(
                {'error': 'Log not found'},
                status=status.HTTP_404_NOT_FOUND
            )


class ErrorLogsView(APIView):
    """
    API endpoint for listing error logs only.
    
    GET /api/logs/errors/
    """
    
    def get(self, request):
        start_date, end_date = parse_date_params(request)
        model = request.query_params.get('model')
        error_type = request.query_params.get('error_type')
        
        queryset = LLMRequestLog.objects.filter(status='error')
        
        # Apply filters
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        if model:
            queryset = queryset.filter(model_name=model)
        if error_type:
            queryset = queryset.filter(error_type=error_type)
        
        # Paginate
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = LLMRequestLogListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = LLMRequestLogListSerializer(queryset[:100], many=True)
        return Response(serializer.data)


# ============================================
# Feedback Endpoints
# ============================================

class FeedbackView(APIView):
    """
    API endpoint for user feedback.
    
    POST /api/feedback/
    GET /api/feedback/
    """
    
    def post(self, request):
        """Submit feedback for an LLM request."""
        serializer = UserFeedbackSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        """List all feedback."""
        start_date, end_date = parse_date_params(request)
        rating = request.query_params.get('rating')
        
        queryset = UserFeedback.objects.all()
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        if rating:
            queryset = queryset.filter(rating=rating)
        
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = UserFeedbackDetailSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = UserFeedbackDetailSerializer(queryset[:100], many=True)
        return Response(serializer.data)


class FeedbackAnalyticsView(APIView):
    """
    API endpoint for feedback analytics.
    
    GET /api/feedback/analytics/
    """
    
    def get(self, request):
        start_date, end_date = parse_date_params(request)
        
        data = metrics_service.get_feedback_analytics(
            start_date=start_date,
            end_date=end_date
        )
        
        serializer = FeedbackAnalyticsSerializer(data)
        return Response(serializer.data)


# ============================================
# Alert Endpoints
# ============================================

class AlertRuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing alert rules.
    """
    queryset = AlertRule.objects.all()
    serializer_class = AlertRuleSerializer
    pagination_class = StandardResultsSetPagination


class AlertLogListView(APIView):
    """
    API endpoint for listing alert logs.
    
    GET /api/alerts/logs/
    """
    
    def get(self, request):
        start_date, end_date = parse_date_params(request)
        acknowledged = request.query_params.get('acknowledged')
        
        queryset = AlertLog.objects.all()
        
        if start_date:
            queryset = queryset.filter(triggered_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(triggered_at__lte=end_date)
        if acknowledged is not None:
            queryset = queryset.filter(acknowledged=acknowledged.lower() == 'true')
        
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = AlertLogSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = AlertLogSerializer(queryset[:100], many=True)
        return Response(serializer.data)


class AlertLogAcknowledgeView(APIView):
    """
    API endpoint to acknowledge an alert.
    
    POST /api/alerts/logs/<id>/acknowledge/
    """
    
    def post(self, request, alert_id):
        try:
            alert_log = AlertLog.objects.get(id=alert_id)
            alert_log.acknowledged = True
            alert_log.acknowledged_at = timezone.now()
            alert_log.save()
            
            serializer = AlertLogSerializer(alert_log)
            return Response(serializer.data)
        except AlertLog.DoesNotExist:
            return Response(
                {'error': 'Alert log not found'},
                status=status.HTTP_404_NOT_FOUND
            )


# ============================================
# Export Endpoints
# ============================================

class ExportCSVView(APIView):
    """
    API endpoint to export data as CSV.
    
    GET /api/export/csv/
    """
    
    def get(self, request):
        start_date, end_date = parse_date_params(request)
        model = request.query_params.get('model')
        status_filter = request.query_params.get('status')
        
        queryset = LLMRequestLog.objects.all()
        
        # Apply filters
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        if model:
            queryset = queryset.filter(model_name=model)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Limit to 10000 records
        queryset = queryset[:10000]
        
        # Create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="llm_logs_export.csv"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'request_id',
            'timestamp',
            'model_name',
            'user_id',
            'prompt_tokens',
            'completion_tokens',
            'total_tokens',
            'latency_ms',
            'cost_estimate',
            'status',
            'error_type',
            'error_message',
        ])
        
        # Write data
        for log in queryset:
            writer.writerow([
                str(log.request_id),
                log.timestamp.isoformat(),
                log.model_name,
                log.user_id or '',
                log.prompt_tokens,
                log.completion_tokens,
                log.total_tokens,
                log.latency_ms,
                str(log.cost_estimate),
                log.status,
                log.error_type,
                log.error_message or '',
            ])
        
        return response


class ExportJSONView(APIView):
    """
    API endpoint to export data as JSON.
    
    GET /api/export/json/
    """
    
    def get(self, request):
        start_date, end_date = parse_date_params(request)
        model = request.query_params.get('model')
        status_filter = request.query_params.get('status')
        include_analytics = request.query_params.get('include_analytics', 'false').lower() == 'true'
        
        queryset = LLMRequestLog.objects.all()
        
        # Apply filters
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        if model:
            queryset = queryset.filter(model_name=model)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Limit to 10000 records
        queryset = queryset[:10000]
        
        # Serialize logs
        serializer = LLMRequestLogListSerializer(queryset, many=True)
        
        export_data = {
            'exported_at': timezone.now().isoformat(),
            'total_records': len(serializer.data),
            'filters': {
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None,
                'model': model,
                'status': status_filter,
            },
            'logs': serializer.data,
        }
        
        # Optionally include analytics
        if include_analytics:
            export_data['analytics'] = {
                'overview': metrics_service.get_overview_metrics(
                    start_date=start_date,
                    end_date=end_date,
                    model=model
                ),
                'model_usage': metrics_service.get_model_usage(
                    start_date=start_date,
                    end_date=end_date
                ),
                'error_breakdown': metrics_service.get_error_metrics(
                    start_date=start_date,
                    end_date=end_date,
                    model=model
                ),
            }
        
        response = HttpResponse(
            json.dumps(export_data, default=str, indent=2),
            content_type='application/json'
        )
        response['Content-Disposition'] = 'attachment; filename="llm_logs_export.json"'
        
        return response


# ============================================
# Available Models Endpoint
# ============================================

class AvailableModelsView(APIView):
    """
    API endpoint to get list of models that have been used.
    
    GET /api/models/
    """
    
    def get(self, request):
        models = LLMRequestLog.objects.values_list(
            'model_name', flat=True
        ).distinct()
        return Response(list(models))
