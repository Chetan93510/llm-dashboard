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


DATABASES = {
'default': {
'ENGINE': os.getenv('DB_ENGINE'),
'NAME': os.getenv('DB_NAME'),
'USER': os.getenv('DB_USER'),
'PASSWORD': os.getenv('DB_PASSWORD'),
'HOST': os.getenv('DB_HOST'),
'PORT': os.getenv('DB_PORT'),
}
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