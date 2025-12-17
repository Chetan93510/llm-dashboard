"""
Authentication views for login, signup, and OTP verification
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .models import EmailOTP


def login_view(request):
    """Login page with Google OAuth and email/password"""
    if request.user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
            
            if user is not None:
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, 'Login successful!')
                return redirect('/')
            else:
                messages.error(request, 'Invalid password')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email')
    
    return render(request, 'auth/login.html')


def signup_view(request):
    """Signup page - directly create account without OTP"""
    if request.user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        full_name = request.POST.get('full_name', '')
        
        # Email format validation
        import re
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not email or not re.match(email_regex, email):
            messages.error(request, 'Please enter a valid email address')
            return render(request, 'auth/signup.html')
        
        # Check for disposable/temporary email domains
        disposable_domains = [
            'tempmail.com', 'throwaway.com', 'mailinator.com', 'guerrillamail.com',
            'temp-mail.org', '10minutemail.com', 'fakeinbox.com', 'trashmail.com',
            'yopmail.com', 'getnada.com', 'maildrop.cc', 'dispostable.com'
        ]
        email_domain = email.split('@')[1] if '@' in email else ''
        if email_domain in disposable_domains:
            messages.error(request, 'Temporary/disposable email addresses are not allowed')
            return render(request, 'auth/signup.html')
        
        # Password validation
        if not password or len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters')
            return render(request, 'auth/signup.html')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match')
            return render(request, 'auth/signup.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered')
            return render(request, 'auth/signup.html')
        
        # Create user directly without OTP
        try:
            # Generate unique username from email
            base_username = email.split('@')[0]
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            
            # Set name
            if full_name:
                name_parts = full_name.split(' ', 1)
                user.first_name = name_parts[0]
                if len(name_parts) > 1:
                    user.last_name = name_parts[1]
                user.save()
            
            # Log user in automatically
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Account created successfully!')
            return redirect('/')
            
        except Exception as e:
            messages.error(request, f'Error creating account: {str(e)}')
    
    return render(request, 'auth/signup.html')


def verify_otp_view(request):
    """OTP verification page"""
    if request.user.is_authenticated:
        return redirect('/')
    
    email = request.session.get('signup_email')
    if not email:
        messages.error(request, 'Please start signup process first')
        return redirect('signup')
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        
        try:
            otp = EmailOTP.objects.filter(
                email=email,
                otp_code=otp_code,
                is_verified=False
            ).latest('created_at')
            
            if not otp.can_attempt():
                messages.error(request, 'OTP expired or maximum attempts reached')
                return render(request, 'auth/verify_otp.html', {'email': email})
            
            otp.attempts += 1
            otp.save()
            
            if otp.otp_code == otp_code and not otp.is_expired():
                # Mark OTP as verified
                otp.is_verified = True
                otp.save()
                
                # Create user
                password = request.session.get('signup_password')
                full_name = request.session.get('signup_full_name', '')
                
                # Split full name into first and last name
                name_parts = full_name.split(' ', 1)
                first_name = name_parts[0] if name_parts else ''
                last_name = name_parts[1] if len(name_parts) > 1 else ''
                
                user = User.objects.create_user(
                    username=email.split('@')[0],
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name
                )
                
                # Login user
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                
                # Clear session
                request.session.pop('signup_email', None)
                request.session.pop('signup_password', None)
                request.session.pop('signup_full_name', None)
                
                messages.success(request, 'Account created successfully!')
                return redirect('/')
            else:
                messages.error(request, 'Invalid OTP code')
                
        except EmailOTP.DoesNotExist:
            messages.error(request, 'Invalid OTP code')
    
    return render(request, 'auth/verify_otp.html', {'email': email})


def resend_otp_view(request):
    """Resend OTP to email"""
    email = request.session.get('signup_email')
    if not email:
        messages.error(request, 'Please start signup process first')
        return redirect('signup')
    
    # Create new OTP
    otp = EmailOTP.create_otp(email)
    
    try:
        send_mail(
            subject='Your OTP for LLM Observability Dashboard',
            message=f'Your new OTP code is: {otp.otp_code}\n\nThis code will expire in 10 minutes.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        messages.success(request, 'New OTP sent to your email!')
    except Exception as e:
        messages.error(request, f'Failed to send OTP: {str(e)}')
    
    return redirect('verify_otp')


def logout_view(request):
    """Logout user"""
    logout(request)
    messages.success(request, 'Logged out successfully!')
    return redirect('login')


# API endpoints for OTP
@api_view(['POST'])
def send_otp_api(request):
    """API endpoint to send OTP"""
    email = request.data.get('email')
    
    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Create OTP
    otp = EmailOTP.create_otp(email)
    
    try:
        send_mail(
            subject='Your OTP for LLM Observability Dashboard',
            message=f'Your OTP code is: {otp.otp_code}\n\nThis code will expire in 10 minutes.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        
        return Response({
            'success': True,
            'message': 'OTP sent successfully',
            'expires_in': '10 minutes'
        })
        
    except Exception as e:
        return Response({
            'error': f'Failed to send OTP: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def verify_otp_api(request):
    """API endpoint to verify OTP"""
    email = request.data.get('email')
    otp_code = request.data.get('otp_code')
    
    if not email or not otp_code:
        return Response({
            'error': 'Email and OTP code are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        otp = EmailOTP.objects.filter(
            email=email,
            otp_code=otp_code,
            is_verified=False
        ).latest('created_at')
        
        if not otp.can_attempt():
            return Response({
                'error': 'OTP expired or maximum attempts reached'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        otp.attempts += 1
        otp.save()
        
        if otp.otp_code == otp_code and not otp.is_expired():
            otp.is_verified = True
            otp.save()
            
            return Response({
                'success': True,
                'message': 'OTP verified successfully'
            })
        else:
            return Response({
                'error': 'Invalid OTP code',
                'attempts_remaining': 3 - otp.attempts
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except EmailOTP.DoesNotExist:
        return Response({
            'error': 'Invalid OTP code'
        }, status=status.HTTP_400_BAD_REQUEST)
