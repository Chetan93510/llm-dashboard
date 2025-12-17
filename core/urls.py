"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from llm.auth_views import (
    login_view, signup_view, verify_otp_view, 
    resend_otp_view, logout_view,
    send_otp_api, verify_otp_api
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Authentication URLs - Custom views MUST come BEFORE allauth
    path('accounts/login/', login_view, name='login'),
    path('accounts/signup/', signup_view, name='signup'),
    path('accounts/verify-otp/', verify_otp_view, name='verify_otp'),
    path('accounts/resend-otp/', resend_otp_view, name='resend_otp'),
    path('accounts/logout/', logout_view, name='logout'),
    path('accounts/', include('allauth.urls')),  # Google OAuth - AFTER custom views
    
    # API endpoints
    path('api/', include('llm.urls')),
    path('api/auth/send-otp/', send_otp_api, name='api_send_otp'),
    path('api/auth/verify-otp/', verify_otp_api, name='api_verify_otp'),
    
    # Frontend pages (served via Django templates)
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
    path('chat/', TemplateView.as_view(template_name='chat.html'), name='chat'),
    path('analytics/', TemplateView.as_view(template_name='analytics.html'), name='analytics'),
    path('logs/', TemplateView.as_view(template_name='logs.html'), name='logs'),
    path('feedback/', TemplateView.as_view(template_name='feedback.html'), name='feedback'),
    path('alerts/', TemplateView.as_view(template_name='alerts.html'), name='alerts'),
]

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0] if settings.STATICFILES_DIRS else None)
