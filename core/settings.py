import os
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')


ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')

# Vercel deployment detection
if os.getenv('VERCEL'):
    ALLOWED_HOSTS.append('.vercel.app')
    ALLOWED_HOSTS.append('localhost')

# Security settings for production
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = False  # Vercel handles SSL
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# CSRF trusted origins for Vercel
_csrf_origins = os.getenv('CSRF_TRUSTED_ORIGINS', '')
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in _csrf_origins.split(',') if origin.strip()]
if os.getenv('VERCEL_URL'):
    CSRF_TRUSTED_ORIGINS.append(f"https://{os.getenv('VERCEL_URL')}")
# Add default for local development
if DEBUG:
    CSRF_TRUSTED_ORIGINS.extend(['http://localhost:8000', 'http://127.0.0.1:8000'])

SITE_ID = 1


INSTALLED_APPS = [
'django.contrib.admin',
'django.contrib.auth',
'django.contrib.contenttypes',
'django.contrib.sessions',
'django.contrib.messages',
'django.contrib.staticfiles',
'django.contrib.sites',


'rest_framework',
'corsheaders',


'allauth',
'allauth.account',
'allauth.socialaccount',
'allauth.socialaccount.providers.google',


'llm',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # 🔥 IMPORTANT

    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'llm.middleware.UserIDMiddleware',  # agar ye file exist karti hai
]




ROOT_URLCONF = 'core.urls'


TEMPLATES = [
{
'BACKEND': 'django.template.backends.django.DjangoTemplates',
'DIRS': [BASE_DIR / 'templates'],
'APP_DIRS': True,
'OPTIONS': {
'context_processors': [
'django.template.context_processors.request',
'django.contrib.auth.context_processors.auth',
'django.contrib.messages.context_processors.messages',
],
},
},
]


AUTHENTICATION_BACKENDS = [
'django.contrib.auth.backends.ModelBackend',
'allauth.account.auth_backends.AuthenticationBackend',
]


# Allauth settings (new format for django-allauth 0.50+)
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'none'

# Redirect URLs after login/logout
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
ACCOUNT_LOGOUT_REDIRECT_URL = '/'


SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True


SOCIALACCOUNT_PROVIDERS = {
'google': {
'APP': {
'client_id': os.getenv('GOOGLE_CLIENT_ID'),
'secret': os.getenv('GOOGLE_CLIENT_SECRET'),
},
'SCOPE': ['profile', 'email'],
}
}


# Database Configuration - SQLite for development
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ============================================
# Groq API Configuration
# ============================================

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GROQ_API_BASE_URL = os.getenv(
    'GROQ_API_BASE_URL',
    'https://api.groq.com/openai/v1'
)

GROQ_DEFAULT_MODEL = os.getenv(
    'GROQ_DEFAULT_MODEL',
    'llama-3.3-70b-versatile'
)

# Token pricing per 1M tokens (input/output) for cost estimation
LLM_TOKEN_PRICING = {
    'llama-3.3-70b-versatile': {'input': 0.59, 'output': 0.79},
    'llama-3.1-70b-versatile': {'input': 0.59, 'output': 0.79},
    'llama-3.1-8b-instant': {'input': 0.05, 'output': 0.08},
    'llama3-70b-8192': {'input': 0.59, 'output': 0.79},
    'llama3-8b-8192': {'input': 0.05, 'output': 0.08},
    'mixtral-8x7b-32768': {'input': 0.24, 'output': 0.24},
    'gemma2-9b-it': {'input': 0.20, 'output': 0.20},
    'default': {'input': 0.50, 'output': 0.50},
}


STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# WhiteNoise for serving static files in production
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


REST_FRAMEWORK = {
'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
'PAGE_SIZE': 50,
}


CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
CORS_ALLOW_ALL_ORIGINS = DEBUG


EMAIL_BACKEND = os.getenv('EMAIL_BACKEND')
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


# Log directory for local development
if not os.getenv('VERCEL'):
    LOG_DIR = BASE_DIR / 'logs'
    LOG_DIR.mkdir(exist_ok=True)
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'file': {
                'class': 'logging.FileHandler',
                'filename': LOG_DIR / 'llm.log',
            },
        },
        'loggers': {
            'llm': {
                'handlers': ['file'],
                'level': 'INFO',
            },
        },
    }
else:
    # Console logging for Vercel (serverless)
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'llm': {
                'handlers': ['console'],
                'level': 'INFO',
            },
        },
    }