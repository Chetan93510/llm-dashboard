from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth.models import User
import uuid


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """Custom adapter to auto-signup users via Google OAuth without asking for email"""
    
    def is_auto_signup_allowed(self, request, sociallogin):
        """Always allow auto-signup for social accounts"""
        return True
    
    def get_unique_username(self, base_username):
        """Generate unique username if base already exists"""
        username = base_username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        return username
    
    def populate_user(self, request, sociallogin, data):
        """Populate user data from social account"""
        user = super().populate_user(request, sociallogin, data)
        
        # Get email from social account
        if sociallogin.account.extra_data.get('email'):
            user.email = sociallogin.account.extra_data['email']
        
        # Set username from email if not set - make unique
        if not user.username and user.email:
            base_username = user.email.split('@')[0]
            user.username = self.get_unique_username(base_username)
        
        # Set first/last name from Google data
        if sociallogin.account.extra_data.get('name'):
            name_parts = sociallogin.account.extra_data['name'].split(' ', 1)
            user.first_name = name_parts[0]
            if len(name_parts) > 1:
                user.last_name = name_parts[1]
        
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """Save user without requiring form"""
        user = sociallogin.user
        user.set_unusable_password()
        
        # Ensure unique username
        if not user.username and user.email:
            base_username = user.email.split('@')[0]
            user.username = self.get_unique_username(base_username)
        elif user.username and User.objects.filter(username=user.username).exists():
            user.username = self.get_unique_username(user.username)
        
        user.save()
        sociallogin.save(request)
        return user
