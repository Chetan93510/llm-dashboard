"""
LLM Observability Dashboard - Alerting System

This module provides alert checking and notification functionality.
"""

import logging
from datetime import timedelta
from decimal import Decimal
from typing import List, Optional

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Avg, Count, Sum, Q
from django.utils import timezone

from .models import LLMRequestLog, AlertRule, AlertLog

logger = logging.getLogger('alerts')


class AlertService:
    """
    Service for checking alert conditions and sending notifications.
    """
    
    def __init__(self):
        """Initialize alert service with configuration from settings."""
        self.default_error_threshold = settings.ALERT_ERROR_RATE_THRESHOLD
        self.default_latency_threshold = settings.ALERT_LATENCY_THRESHOLD_MS
        self.default_token_multiplier = settings.ALERT_TOKEN_SPIKE_MULTIPLIER
        self.email_recipients = [
            email.strip() 
            for email in settings.ALERT_EMAIL_RECIPIENTS 
            if email.strip()
        ]
    
    def check_all_alerts(self, time_window_minutes: int = 60) -> List[AlertLog]:
        """
        Check all active alert rules.
        
        Args:
            time_window_minutes: Time window for metric calculation
            
        Returns:
            List of triggered AlertLog instances
        """
        active_rules = AlertRule.objects.filter(is_active=True)
        triggered_alerts = []
        
        for rule in active_rules:
            alert_log = self._check_rule(rule, time_window_minutes)
            if alert_log:
                triggered_alerts.append(alert_log)
        
        return triggered_alerts
    
    def _check_rule(
        self,
        rule: AlertRule,
        time_window_minutes: int
    ) -> Optional[AlertLog]:
        """
        Check a single alert rule.
        
        Args:
            rule: The alert rule to check
            time_window_minutes: Time window for metric calculation
            
        Returns:
            AlertLog if triggered, None otherwise
        """
        # Calculate time window
        end_time = timezone.now()
        start_time = end_time - timedelta(minutes=time_window_minutes)
        
        # Get recent logs
        queryset = LLMRequestLog.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time
        )
        
        total_count = queryset.count()
        if total_count == 0:
            return None
        
        # Check based on metric type
        if rule.metric_type == 'error_rate':
            return self._check_error_rate(rule, queryset, total_count)
        elif rule.metric_type == 'latency':
            return self._check_latency(rule, queryset)
        elif rule.metric_type == 'token_spike':
            return self._check_token_spike(rule, queryset, time_window_minutes)
        
        return None
    
    def _check_error_rate(
        self,
        rule: AlertRule,
        queryset,
        total_count: int
    ) -> Optional[AlertLog]:
        """Check error rate threshold."""
        error_count = queryset.filter(status='error').count()
        error_rate = (error_count / total_count) * 100 if total_count > 0 else 0
        
        if error_rate >= rule.threshold:
            message = (
                f"Error rate alert: {error_rate:.2f}% "
                f"(threshold: {rule.threshold}%). "
                f"{error_count} errors out of {total_count} total requests."
            )
            return self._trigger_alert(rule, error_rate, message)
        
        return None
    
    def _check_latency(
        self,
        rule: AlertRule,
        queryset
    ) -> Optional[AlertLog]:
        """Check latency threshold."""
        # Calculate P95 latency
        success_queryset = queryset.filter(status='success')
        latencies = list(
            success_queryset.values_list('latency_ms', flat=True).order_by('latency_ms')
        )
        
        if not latencies:
            return None
        
        p95_index = int(len(latencies) * 0.95)
        p95_latency = latencies[min(p95_index, len(latencies) - 1)]
        
        if p95_latency >= rule.threshold:
            message = (
                f"Latency alert: P95 latency is {p95_latency}ms "
                f"(threshold: {rule.threshold}ms). "
                f"Calculated from {len(latencies)} requests."
            )
            return self._trigger_alert(rule, p95_latency, message)
        
        return None
    
    def _check_token_spike(
        self,
        rule: AlertRule,
        queryset,
        time_window_minutes: int
    ) -> Optional[AlertLog]:
        """Check for token usage spike."""
        # Get current period token usage
        current_tokens = queryset.aggregate(
            total=Sum('total_tokens')
        )['total'] or 0
        
        # Get previous period for comparison
        end_time = timezone.now() - timedelta(minutes=time_window_minutes)
        start_time = end_time - timedelta(minutes=time_window_minutes)
        
        previous_queryset = LLMRequestLog.objects.filter(
            timestamp__gte=start_time,
            timestamp__lte=end_time
        )
        
        previous_tokens = previous_queryset.aggregate(
            total=Sum('total_tokens')
        )['total'] or 0
        
        # Calculate spike ratio
        if previous_tokens > 0:
            spike_ratio = current_tokens / previous_tokens
        else:
            spike_ratio = float(current_tokens) if current_tokens > 0 else 0
        
        if spike_ratio >= rule.threshold:
            message = (
                f"Token spike alert: {spike_ratio:.2f}x increase "
                f"(threshold: {rule.threshold}x). "
                f"Current: {current_tokens} tokens, "
                f"Previous period: {previous_tokens} tokens."
            )
            return self._trigger_alert(rule, spike_ratio, message)
        
        return None
    
    def _trigger_alert(
        self,
        rule: AlertRule,
        metric_value: float,
        message: str
    ) -> AlertLog:
        """
        Create alert log and send notifications.
        
        Args:
            rule: The triggered alert rule
            metric_value: The value that triggered the alert
            message: Alert message
            
        Returns:
            Created AlertLog instance
        """
        # Log to console
        logger.warning(f"ALERT TRIGGERED - {rule.name}: {message}")
        
        # Create alert log
        alert_log = AlertLog.objects.create(
            alert_rule=rule,
            message=message,
            metric_value=metric_value
        )
        
        # Update last triggered time
        rule.last_triggered_at = timezone.now()
        rule.save(update_fields=['last_triggered_at'])
        
        # Send email if configured
        if rule.notify_email and self.email_recipients:
            self._send_email_notification(rule, message)
        
        return alert_log
    
    def _send_email_notification(
        self,
        rule: AlertRule,
        message: str
    ) -> bool:
        """
        Send email notification for an alert.
        
        Args:
            rule: The triggered alert rule
            message: Alert message
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            subject = f"[LLM Observability] Alert: {rule.name}"
            body = f"""
Alert Triggered: {rule.name}

{message}

Alert Details:
- Metric Type: {dict(AlertRule.METRIC_TYPE_CHOICES).get(rule.metric_type, rule.metric_type)}
- Threshold: {rule.threshold}
- Triggered At: {timezone.now().isoformat()}

---
This is an automated alert from the LLM Observability Dashboard.
            """
            
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.EMAIL_HOST_USER or 'alerts@llm-observability.local',
                recipient_list=self.email_recipients,
                fail_silently=False
            )
            
            logger.info(f"Alert email sent to {len(self.email_recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")
            return False
    
    def create_default_rules(self) -> List[AlertRule]:
        """
        Create default alert rules if none exist.
        
        Returns:
            List of created AlertRule instances
        """
        created_rules = []
        
        defaults = [
            {
                'name': 'High Error Rate',
                'description': 'Alert when error rate exceeds 5%',
                'metric_type': 'error_rate',
                'threshold': self.default_error_threshold * 100,  # Convert to percentage
            },
            {
                'name': 'High Latency',
                'description': 'Alert when P95 latency exceeds 5 seconds',
                'metric_type': 'latency',
                'threshold': self.default_latency_threshold,
            },
            {
                'name': 'Token Usage Spike',
                'description': 'Alert when token usage is 3x the previous period',
                'metric_type': 'token_spike',
                'threshold': self.default_token_multiplier,
            },
        ]
        
        for rule_data in defaults:
            rule, created = AlertRule.objects.get_or_create(
                name=rule_data['name'],
                defaults=rule_data
            )
            if created:
                created_rules.append(rule)
                logger.info(f"Created default alert rule: {rule.name}")
        
        return created_rules


# Create singleton instance
alert_service = AlertService()
