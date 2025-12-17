"""
LLM Observability Dashboard - URL Configuration for llm app
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

# Create router for viewsets
router = DefaultRouter()
router.register(r'rules', views.AlertRuleViewSet, basename='alert-rules')

urlpatterns = [
    # LLM Prompt endpoint
    path('llm/prompt/', views.LLMPromptView.as_view(), name='llm-prompt'),
    
    # Metrics endpoints
    path('metrics/overview/', views.MetricsOverviewView.as_view(), name='metrics-overview'),
    path('metrics/token-usage/', views.TokenUsageView.as_view(), name='metrics-token-usage'),
    path('metrics/latency/', views.LatencyMetricsView.as_view(), name='metrics-latency'),
    path('metrics/errors/', views.ErrorMetricsView.as_view(), name='metrics-errors'),
    path('metrics/model-usage/', views.ModelUsageView.as_view(), name='metrics-model-usage'),
    path('metrics/daily-stats/', views.DailyStatsView.as_view(), name='metrics-daily-stats'),
    
    # Logs endpoints
    path('logs/', views.LogsListView.as_view(), name='logs-list'),
    path('logs/errors/', views.ErrorLogsView.as_view(), name='logs-errors'),
    path('logs/<uuid:request_id>/', views.LogDetailView.as_view(), name='logs-detail'),
    
    # Feedback endpoints
    path('feedback/', views.FeedbackView.as_view(), name='feedback'),
    path('feedback/analytics/', views.FeedbackAnalyticsView.as_view(), name='feedback-analytics'),
    
    # Alert endpoints
    path('alerts/', include(router.urls)),
    path('alerts/logs/', views.AlertLogListView.as_view(), name='alert-logs'),
    path('alerts/logs/<uuid:alert_id>/acknowledge/', views.AlertLogAcknowledgeView.as_view(), name='alert-acknowledge'),
    
    # Export endpoints
    path('export/csv/', views.ExportCSVView.as_view(), name='export-csv'),
    path('export/json/', views.ExportJSONView.as_view(), name='export-json'),
    
    # Utility endpoints
    path('models/', views.AvailableModelsView.as_view(), name='available-models'),
]
