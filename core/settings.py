import os
from pathlib import Path
from dotenv import load_dotenv


load_dotenv()


BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 'yes')


ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')


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


ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_EMAIL_VERIFICATION = 'none'


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


# Database Configuration
DB_ENGINE = os.getenv('DB_ENGINE', 'django.db.backends.sqlite3')
DB_NAME = os.getenv('DB_NAME', BASE_DIR / 'db.sqlite3')

if 'sqlite3' in DB_ENGINE:
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': DB_NAME if isinstance(DB_NAME, Path) else BASE_DIR / DB_NAME,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': DB_ENGINE,
            'NAME': DB_NAME,
            'USER': os.getenv('DB_USER'),
            'PASSWORD': os.getenv('DB_PASSWORD'),
            'HOST': os.getenv('DB_HOST'),
            'PORT': os.getenv('DB_PORT'),
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
STATICFILES_DIRS = [BASE_DIR / 'static']


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


REST_FRAMEWORK = {
'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
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