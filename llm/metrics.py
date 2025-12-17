"""
LLM Observability Dashboard - Metrics Aggregation Services

This module provides services for calculating and aggregating
LLM usage metrics for the dashboard.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional
from collections import defaultdict

from django.db.models import (
    Sum, Avg, Count, Min, Max, F, Q,
    Value, CharField, FloatField
)
from django.db.models.functions import (
    TruncHour, TruncDay, TruncMonth, Coalesce,
    Cast
)
from django.utils import timezone

from .models import LLMRequestLog, UserFeedback


class MetricsService:
    """
    Service for calculating and aggregating LLM usage metrics.
    """
    
    @staticmethod
    def get_overview_metrics(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        model: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get overview metrics for the dashboard.
        
        Args:
            start_date: Filter start date
            end_date: Filter end date
            model: Filter by model name
            user_id: Filter by user (for isolation)
            
        Returns:
            Dictionary with overview metrics
        """
        queryset = LLMRequestLog.objects.all()
        
        # CRITICAL: Filter by user first
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Apply filters
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        if model:
            queryset = queryset.filter(model_name=model)
        
        # Calculate basic metrics
        total_calls = queryset.count()
        
        if total_calls == 0:
            return {
                'total_calls': 0,
                'total_tokens': 0,
                'total_cost': Decimal('0'),
                'avg_latency_ms': 0,
                'p95_latency_ms': 0,
                'error_rate': 0,
                'success_count': 0,
                'error_count': 0,
            }
        
        # Aggregate metrics
        aggregates = queryset.aggregate(
            total_tokens=Coalesce(Sum('total_tokens'), 0),
            total_cost=Coalesce(Sum('cost_estimate'), Decimal('0')),
            avg_latency=Coalesce(Avg('latency_ms'), 0.0),
        )
        
        # Count by status
        success_count = queryset.filter(status='success').count()
        error_count = queryset.filter(status='error').count()
        
        # Calculate P95 latency
        latencies = list(queryset.values_list('latency_ms', flat=True).order_by('latency_ms'))
        p95_index = int(len(latencies) * 0.95)
        p95_latency = latencies[p95_index] if latencies else 0
        
        # Calculate error rate
        error_rate = (error_count / total_calls) * 100 if total_calls > 0 else 0
        
        return {
            'total_calls': total_calls,
            'total_tokens': aggregates['total_tokens'],
            'total_cost': aggregates['total_cost'],
            'avg_latency_ms': round(aggregates['avg_latency'], 2),
            'p95_latency_ms': p95_latency,
            'error_rate': round(error_rate, 2),
            'success_count': success_count,
            'error_count': error_count,
        }
    
    @staticmethod
    def get_token_usage_over_time(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        model: Optional[str] = None,
        group_by: str = 'day',
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get token usage aggregated over time.
        
        Args:
            start_date: Filter start date
            end_date: Filter end date
            model: Filter by model name
            group_by: Grouping period ('hour', 'day', 'month')
            user_id: Filter by user
            
        Returns:
            List of token usage records by period
        """
        queryset = LLMRequestLog.objects.filter(status='success')
        
        # CRITICAL: Filter by user first
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Apply filters
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        if model:
            queryset = queryset.filter(model_name=model)
        
        # Select truncation function based on grouping
        trunc_func = {
            'hour': TruncHour,
            'day': TruncDay,
            'month': TruncMonth,
        }.get(group_by, TruncDay)
        
        # Aggregate by period
        data = queryset.annotate(
            period=trunc_func('timestamp')
        ).values('period').annotate(
            prompt_tokens=Coalesce(Sum('prompt_tokens'), 0),
            completion_tokens=Coalesce(Sum('completion_tokens'), 0),
            total_tokens=Coalesce(Sum('total_tokens'), 0),
            cost=Coalesce(Sum('cost_estimate'), Decimal('0')),
        ).order_by('period')
        
        return [
            {
                'period': item['period'].isoformat() if item['period'] else None,
                'prompt_tokens': item['prompt_tokens'],
                'completion_tokens': item['completion_tokens'],
                'total_tokens': item['total_tokens'],
                'cost': item['cost'],
            }
            for item in data
        ]
    
    @staticmethod
    def get_latency_metrics(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get latency metrics grouped by model.
        
        Args:
            start_date: Filter start date
            end_date: Filter end date
            user_id: Filter by user
            
        Returns:
            List of latency metrics per model
        """
        queryset = LLMRequestLog.objects.filter(status='success')
        
        # CRITICAL: Filter by user first
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Apply filters
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        # Get unique models
        models = queryset.values_list('model_name', flat=True).distinct()
        
        results = []
        for model in models:
            model_queryset = queryset.filter(model_name=model)
            
            # Calculate statistics
            stats = model_queryset.aggregate(
                avg_latency=Coalesce(Avg('latency_ms'), 0.0),
                min_latency=Coalesce(Min('latency_ms'), 0),
                max_latency=Coalesce(Max('latency_ms'), 0),
                call_count=Count('request_id'),
            )
            
            # Calculate P95
            latencies = list(model_queryset.values_list('latency_ms', flat=True).order_by('latency_ms'))
            p95_index = int(len(latencies) * 0.95) if latencies else 0
            p95_latency = latencies[p95_index] if latencies and p95_index < len(latencies) else 0
            
            results.append({
                'model_name': model,
                'avg_latency_ms': round(stats['avg_latency'], 2),
                'min_latency_ms': stats['min_latency'],
                'max_latency_ms': stats['max_latency'],
                'p95_latency_ms': p95_latency,
                'call_count': stats['call_count'],
            })
        
        return results
    
    @staticmethod
    def get_error_metrics(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        model: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get error metrics breakdown.
        
        Args:
            start_date: Filter start date
            end_date: Filter end date
            model: Filter by model name
            user_id: Filter by user
            
        Returns:
            List of error counts by type
        """
        queryset = LLMRequestLog.objects.filter(status='error')
        
        # CRITICAL: Filter by user first
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Apply filters
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        if model:
            queryset = queryset.filter(model_name=model)
        
        total_errors = queryset.count()
        
        # Group by error type
        error_counts = queryset.values('error_type').annotate(
            count=Count('request_id')
        ).order_by('-count')
        
        return [
            {
                'error_type': item['error_type'],
                'count': item['count'],
                'percentage': round((item['count'] / total_errors) * 100, 2) if total_errors > 0 else 0,
            }
            for item in error_counts
        ]
    
    @staticmethod
    def get_model_usage(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get usage breakdown by model.
        
        Args:
            start_date: Filter start date
            end_date: Filter end date
            user_id: Filter by user
            
        Returns:
            List of usage statistics per model
        """
        queryset = LLMRequestLog.objects.all()
        
        # CRITICAL: Filter by user first
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Apply filters
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        total_calls = queryset.count()
        
        # Group by model
        model_stats = queryset.values('model_name').annotate(
            call_count=Count('request_id'),
            total_tokens=Coalesce(Sum('total_tokens'), 0),
            total_cost=Coalesce(Sum('cost_estimate'), Decimal('0')),
        ).order_by('-call_count')
        
        return [
            {
                'model_name': item['model_name'],
                'call_count': item['call_count'],
                'total_tokens': item['total_tokens'],
                'total_cost': item['total_cost'],
                'percentage': round((item['call_count'] / total_calls) * 100, 2) if total_calls > 0 else 0,
            }
            for item in model_stats
        ]
    
    @staticmethod
    def get_feedback_analytics(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Get feedback analytics.
        
        Args:
            start_date: Filter start date
            end_date: Filter end date
            
        Returns:
            Dictionary with feedback statistics
        """
        queryset = UserFeedback.objects.all()
        
        # Apply filters
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        total_feedback = queryset.count()
        thumbs_up = queryset.filter(rating='thumbs_up').count()
        thumbs_down = queryset.filter(rating='thumbs_down').count()
        
        return {
            'total_feedback': total_feedback,
            'thumbs_up_count': thumbs_up,
            'thumbs_down_count': thumbs_down,
            'thumbs_up_percentage': round((thumbs_up / total_feedback) * 100, 2) if total_feedback > 0 else 0,
            'thumbs_down_percentage': round((thumbs_down / total_feedback) * 100, 2) if total_feedback > 0 else 0,
        }
    
    @staticmethod
    def get_daily_stats(days: int = 7, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get daily statistics for the last N days.
        
        Args:
            days: Number of days to retrieve
            user_id: Filter by user
            
        Returns:
            List of daily statistics
        """
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        queryset = LLMRequestLog.objects.filter(
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        
        # CRITICAL: Filter by user
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Group by day
        daily_stats = queryset.annotate(
            day=TruncDay('timestamp')
        ).values('day').annotate(
            total_calls=Count('request_id'),
            success_calls=Count('request_id', filter=Q(status='success')),
            error_calls=Count('request_id', filter=Q(status='error')),
            total_tokens=Coalesce(Sum('total_tokens'), 0),
            total_cost=Coalesce(Sum('cost_estimate'), Decimal('0')),
            avg_latency=Coalesce(Avg('latency_ms'), 0.0),
        ).order_by('day')
        
        return [
            {
                'date': item['day'].date().isoformat() if item['day'] else None,
                'total_calls': item['total_calls'],
                'success_calls': item['success_calls'],
                'error_calls': item['error_calls'],
                'total_tokens': item['total_tokens'],
                'total_cost': item['total_cost'],
                'avg_latency_ms': round(item['avg_latency'], 2),
                'error_rate': round((item['error_calls'] / item['total_calls']) * 100, 2) if item['total_calls'] > 0 else 0,
            }
            for item in daily_stats
        ]


# Create singleton instance
metrics_service = MetricsService()
