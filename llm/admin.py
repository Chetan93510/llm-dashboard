"""
LLM Observability Dashboard - Django Admin Configuration
"""

from django.contrib import admin
from .models import LLMRequestLog, UserFeedback, AlertRule, AlertLog


@admin.register(LLMRequestLog)
class LLMRequestLogAdmin(admin.ModelAdmin):
    """Admin configuration for LLM request logs."""
    
    list_display = [
        'request_id',
        'model_name',
        'status',
        'total_tokens',
        'latency_ms',
        'cost_estimate',
        'timestamp',
    ]
    
    list_filter = [
        'status',
        'model_name',
        'error_type',
        'timestamp',
    ]
    
    search_fields = [
        'request_id',
        'user_id',
        'model_name',
        'prompt_text',
        'error_message',
    ]
    
    readonly_fields = [
        'request_id',
        'timestamp',
    ]
    
    ordering = ['-timestamp']
    
    date_hierarchy = 'timestamp'
    
    fieldsets = (
        ('Request Info', {
            'fields': ('request_id', 'user_id', 'model_name', 'timestamp')
        }),
        ('Content', {
            'fields': ('prompt_text', 'response_text'),
            'classes': ('collapse',),
        }),
        ('Tokens & Cost', {
            'fields': ('prompt_tokens', 'completion_tokens', 'total_tokens', 'cost_estimate')
        }),
        ('Performance', {
            'fields': ('latency_ms',)
        }),
        ('Status', {
            'fields': ('status', 'error_type', 'error_message')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',),
        }),
    )


@admin.register(UserFeedback)
class UserFeedbackAdmin(admin.ModelAdmin):
    """Admin configuration for user feedback."""
    
    list_display = [
        'id',
        'request',
        'rating',
        'user_id',
        'created_at',
    ]
    
    list_filter = [
        'rating',
        'created_at',
    ]
    
    search_fields = [
        'id',
        'request__request_id',
        'user_id',
        'comment',
    ]
    
    readonly_fields = [
        'id',
        'created_at',
    ]
    
    ordering = ['-created_at']


@admin.register(AlertRule)
class AlertRuleAdmin(admin.ModelAdmin):
    """Admin configuration for alert rules."""
    
    list_display = [
        'name',
        'metric_type',
        'threshold',
        'is_active',
        'notify_email',
        'last_triggered_at',
    ]
    
    list_filter = [
        'metric_type',
        'is_active',
        'notify_email',
    ]
    
    search_fields = [
        'name',
        'description',
    ]
    
    readonly_fields = [
        'id',
        'created_at',
        'updated_at',
        'last_triggered_at',
    ]
    
    ordering = ['-created_at']


@admin.register(AlertLog)
class AlertLogAdmin(admin.ModelAdmin):
    """Admin configuration for alert logs."""
    
    list_display = [
        'id',
        'alert_rule',
        'metric_value',
        'acknowledged',
        'triggered_at',
    ]
    
    list_filter = [
        'acknowledged',
        'triggered_at',
        'alert_rule',
    ]
    
    search_fields = [
        'message',
        'alert_rule__name',
    ]
    
    readonly_fields = [
        'id',
        'triggered_at',
    ]
    
    ordering = ['-triggered_at']
    
    actions = ['acknowledge_alerts']
    
    @admin.action(description='Acknowledge selected alerts')
    def acknowledge_alerts(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(acknowledged=True, acknowledged_at=timezone.now())
        self.message_user(request, f'{updated} alerts acknowledged.')
