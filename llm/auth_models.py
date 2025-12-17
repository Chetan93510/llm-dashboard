"""
Authentication models for OTP verification
"""

import random
from datetime import timedelta
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.conf import settings


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
        expiry_time = self.created_at + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
        return timezone.now() > expiry_time
    
    def can_attempt(self):
        """Check if user can still attempt verification"""
        return self.attempts < 3 and not self.is_expired()
    
    @staticmethod
    def generate_otp():
        """Generate a random 6-digit OTP"""
        return str(random.randint(100000, 999999))
    
    @classmethod
    def create_otp(cls, email):
        """Create a new OTP for an email"""
        # Invalidate old OTPs for this email
        cls.objects.filter(email=email, is_verified=False).update(is_verified=True)
        
        # Create new OTP
        otp_code = cls.generate_otp()
        return cls.objects.create(email=email, otp_code=otp_code)
