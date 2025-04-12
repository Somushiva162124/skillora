import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: Keep the secret key secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'fallback_default_key')  # Add a default fallback for development

# Debug mode (Turn off in production)
DEBUG = False

ALLOWED_HOSTS = ['skillora.onrender.com', 'www.skillora.com', 'skillora.vercel.app' '127.0.0.1', 'localhost']

 # For development, change for deployment

# Installed applications
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'core.apps.CoreConfig',
 # CKEditor upload functionality
    'django_ckeditor_5',  # CKEditor 5
    'whitenoise.runserver_nostatic',  # Add Whitenoise here
]

# Middleware settings
MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Root URL configuration
ROOT_URLCONF = 'online_learning.urls'

# Templates configuration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR / 'core' / 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]



DJANGO_ADMIN_INTERFACE = {
    'theme': 'dark',  # You can switch to 'light' or 'auto' if needed
}

# WSGI Application
WSGI_APPLICATION = 'online_learning.wsgi.application'

# Database Configuration (Using SQLite by default)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# CKEditor 5 Configuration
CKEDITOR_5_CONFIGS = {
    'default': {
        'extends': 'django_ckeditor_5.configs.base',
        "toolbar": [
            "heading", "|",
            "bold", "italic", "underline", "strike", "|",
            "numberedList", "bulletedList", "|",
            "blockQuote", "code", "link", "horizontalLine", "|",
            "undo", "redo",
        ],
        "upload": {
            "image": {
                "types": ["jpeg", "png", "gif", "webp"]
            }
        },
    }
}

# CKEditor Upload Path and Restrictions
CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_RESTRICT_BY_USER = True  # Restrict file uploads to the user

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static Files
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR,'core', 'static')]  # Ensure this is correct

# Collect Static Files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media Files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Authentication
AUTH_USER_MODEL = 'core.CustomUser'

# Redirects after login and logout
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'  # Redirect after login
LOGOUT_REDIRECT_URL = '/'  # Redirect after logout

# CSRF and Session Security (For local development, change to False if not using HTTPS)
CSRF_COOKIE_SECURE = True  # Change to True in production
SESSION_COOKIE_SECURE = True  # Change to True in production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
