"""
LLM Observability Dashboard - Database Models

This module defines the core database models for tracking LLM API calls,
user feedback, and alert rules.
"""

import uuid
from django.db import models
from django.utils import timezone


class LLMRequestLog(models.Model):
    """
    Model to store logs of all LLM API requests.
    
    Each record represents a single LLM API call with all relevant
    metadata including tokens, latency, cost, and error information.
    """
    
    # Status choices for LLM requests
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('error', 'Error'),
    ]
    
    # Error type choices
    ERROR_TYPE_CHOICES = [
        ('none', 'None'),
        ('timeout', 'Timeout'),
        ('rate_limit', 'Rate Limit'),
        ('invalid_prompt', 'Invalid Prompt'),
        ('provider_error', 'Provider Error'),
        ('authentication', 'Authentication Error'),
        ('network', 'Network Error'),
        ('unknown', 'Unknown Error'),
    ]
    
    # Primary identifier
    request_id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for this request"
    )
    
    # User information (nullable for anonymous requests)
    user_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="User identifier who made the request"
    )
    
    # Model information
    model_name = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Name of the LLM model used"
    )
    
    # Request/Response content
    prompt_text = models.TextField(
        help_text="The prompt sent to the LLM"
    )
    response_text = models.TextField(
        null=True,
        blank=True,
        help_text="The response from the LLM"
    )
    
    # Token usage
    prompt_tokens = models.IntegerField(
        default=0,
        help_text="Number of tokens in the prompt"
    )
    completion_tokens = models.IntegerField(
        default=0,
        help_text="Number of tokens in the completion"
    )
    total_tokens = models.IntegerField(
        default=0,
        help_text="Total tokens used (prompt + completion)"
    )
    
    # Performance metrics
    latency_ms = models.IntegerField(
        default=0,
        help_text="Request latency in milliseconds"
    )
    
    # Cost tracking
    cost_estimate = models.DecimalField(
        max_digits=10,
        decimal_places=6,
        default=0,
        help_text="Estimated cost in USD"
    )
    
    # Status and error handling
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='success',
        db_index=True,
        help_text="Request status"
    )
    error_type = models.CharField(
        max_length=50,
        choices=ERROR_TYPE_CHOICES,
        default='none',
        db_index=True,
        help_text="Type of error if request failed"
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Detailed error message"
    )
    
    # Timestamp
    timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="When the request was made"
    )
    
    # Additional metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional request metadata"
    )
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'LLM Request Log'
        verbose_name_plural = 'LLM Request Logs'
        indexes = [
            models.Index(fields=['timestamp', 'status']),
            models.Index(fields=['model_name', 'timestamp']),
            models.Index(fields=['error_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.model_name} - {self.status} - {self.timestamp}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate total tokens if not set
        if self.total_tokens == 0:
            self.total_tokens = self.prompt_tokens + self.completion_tokens
        super().save(*args, **kwargs)


class UserFeedback(models.Model):
    """
    Model to store user feedback on LLM responses.
    
    Allows users to rate responses with thumbs up/down and
    provide optional comments.
    """
    
    RATING_CHOICES = [
        ('thumbs_up', 'Thumbs Up'),
        ('thumbs_down', 'Thumbs Down'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    request = models.ForeignKey(
        LLMRequestLog,
        on_delete=models.CASCADE,
        related_name='feedback',
        help_text="The LLM request this feedback is for"
    )
    
    rating = models.CharField(
        max_length=20,
        choices=RATING_CHOICES,
        help_text="User rating"
    )
    
    comment = models.TextField(
        null=True,
        blank=True,
        help_text="Optional user comment"
    )
    
    user_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="User who provided feedback"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When feedback was submitted"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'User Feedback'
        verbose_name_plural = 'User Feedback'
    
    def __str__(self):
        return f"{self.rating} for {self.request_id}"


class AlertRule(models.Model):
    """
    Model to define alert rules for monitoring LLM metrics.
    
    Supports different metric types with configurable thresholds.
    """
    
    METRIC_TYPE_CHOICES = [
        ('error_rate', 'Error Rate'),
        ('latency', 'Latency'),
        ('token_spike', 'Token Spike'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    name = models.CharField(
        max_length=255,
        help_text="Name of the alert rule"
    )
    
    description = models.TextField(
        null=True,
        blank=True,
        help_text="Description of what this alert monitors"
    )
    
    metric_type = models.CharField(
        max_length=50,
        choices=METRIC_TYPE_CHOICES,
        help_text="Type of metric to monitor"
    )
    
    threshold = models.FloatField(
        help_text="Threshold value that triggers the alert"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this alert rule is active"
    )
    
    notify_email = models.BooleanField(
        default=False,
        help_text="Send email notification when triggered"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True
    )
    
    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    # Track last trigger time to prevent alert flooding
    last_triggered_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this alert was last triggered"
    )
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Alert Rule'
        verbose_name_plural = 'Alert Rules'
    
    def __str__(self):
        return f"{self.name} ({self.metric_type})"


class AlertLog(models.Model):
    """
    Model to store a history of triggered alerts.
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    alert_rule = models.ForeignKey(
        AlertRule,
        on_delete=models.CASCADE,
        related_name='logs',
        help_text="The alert rule that was triggered"
    )
    
    message = models.TextField(
        help_text="Alert message"
    )
    
    metric_value = models.FloatField(
        help_text="The metric value that triggered the alert"
    )
    
    triggered_at = models.DateTimeField(
        auto_now_add=True
    )
    
    acknowledged = models.BooleanField(
        default=False,
        help_text="Whether this alert has been acknowledged"
    )
    
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    class Meta:
        ordering = ['-triggered_at']
        verbose_name = 'Alert Log'
        verbose_name_plural = 'Alert Logs'
    
    def __str__(self):
        return f"{self.alert_rule.name} - {self.triggered_at}"


# ============================================
# Authentication Models
# ============================================

class EmailOTP(models.Model):
    """
    Model to store OTP codes for email verification
    """
    email = models.EmailField(help_text="Email address for OTP")
    otp_code = models.CharField(max_length=6, help_text="6-digit OTP code")
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0, help_text="Number of verification attempts")
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Email OTP"
        verbose_name_plural = "Email OTPs"
    
    def __str__(self):
        return f"{self.email} - {self.otp_code} ({'Verified' if self.is_verified else 'Pending'})"
    
    def is_expired(self):
        """Check if OTP has expired"""
        from datetime import timedelta
        expiry_time = self.created_at + timedelta(minutes=10)
        return timezone.now() > expiry_time
    
    def can_attempt(self):
        """Check if user can still attempt verification"""
        return self.attempts < 3 and not self.is_expired()
    
    @staticmethod
    def generate_otp():
        """Generate a random 6-digit OTP"""
        import random
        return str(random.randint(100000, 999999))
    
    @classmethod
    def create_otp(cls, email):
        """Create a new OTP for an email"""
        # Invalidate old OTPs for this email
        cls.objects.filter(email=email, is_verified=False).update(is_verified=True)
        
        # Create new OTP
        otp_code = cls.generate_otp()
        return cls.objects.create(email=email, otp_code=otp_code)
