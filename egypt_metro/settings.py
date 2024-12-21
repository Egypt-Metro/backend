"""
Django settings for egypt_metro project.

Generated by 'django-admin startproject' using Django 5.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

from pathlib import Path  # File path helper
import os  # Operating system dependent functionality
import dj_database_url    # type: ignore # Parse database URLs
from dotenv import load_dotenv  # Load environment variables from .env file
from datetime import timedelta  # Time delta for JWT tokens
from corsheaders.defaults import default_headers  # Default headers for CORS
from decouple import config
from datetime import datetime

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent  # Base directory for the project

# Load the appropriate .env file based on an environment variable
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")  # Default to dev
dotenv_path = BASE_DIR / f"env/.env.{ENVIRONMENT}"
load_dotenv(dotenv_path)

# Check if the .env file exists and load it
if dotenv_path.is_file():
    load_dotenv(dotenv_path)
else:
    raise FileNotFoundError(f"Environment file not found: {dotenv_path}")

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")  # Secret key for Django
DEBUG = os.getenv("DEBUG", "False") == "True"  # Default to False
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="").split(",")

# Set API start time to the application's boot time
API_START_TIME = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",  # Admin panel
    "django.contrib.auth",  # Authentication framework
    "django.contrib.contenttypes",  # Content types framework
    "django.contrib.sessions",  # Sessions framework
    "django.contrib.messages",  # Messages framework
    "django.contrib.staticfiles",  # Static files

    # External packages
    "allauth",  # Authentication
    "allauth.account",  # Account management
    "allauth.socialaccount",  # Social authentication
    "allauth.socialaccount.providers.google",  # Google OAuth provider
    "rest_framework",  # REST framework
    "rest_framework_simplejwt",  # JWT authentication
    "corsheaders",  # CORS headers
    'drf_yasg',     # Swagger
    # "debug_toolbar",  # Debug toolbar

    # Custom apps
    "apps.users.apps.UsersConfig",  # Users app
    "apps.stations.apps.StationsConfig",  # Stations app
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",  # Security middleware
    "django.contrib.sessions.middleware.SessionMiddleware",  # Session middleware
    "django.middleware.common.CommonMiddleware",  # Common middleware
    "django.middleware.csrf.CsrfViewMiddleware",  # CSRF middleware
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # Authentication middleware
    "django.contrib.messages.middleware.MessageMiddleware",  # Messages middleware
    "django.middleware.clickjacking.XFrameOptionsMiddleware",  # Clickjacking middleware
    "corsheaders.middleware.CorsMiddleware",  # CORS middleware
    "whitenoise.middleware.WhiteNoiseMiddleware",  # WhiteNoise middleware
    "allauth.account.middleware.AccountMiddleware",  # Account middleware
    # "debug_toolbar.middleware.DebugToolbarMiddleware",  # Debug toolbar middleware
]

ROOT_URLCONF = "egypt_metro.urls"  # Root URL configuration
WSGI_APPLICATION = "egypt_metro.wsgi.application"  # WSGI application

# CORS settings
CORS_ALLOW_ALL_ORIGINS = (
    os.getenv("CORS_ALLOW_ALL_ORIGINS", "False") == "True"
)  # Default to False

if not CORS_ALLOW_ALL_ORIGINS:
    CORS_ALLOWED_ORIGINS = [
        "https://backend-54v5.onrender.com",
        "http://localhost:8000",
    ]

CORS_ALLOW_HEADERS = list(default_headers) + [  # Default headers + custom headers
    "Authorization",  # Authorization header
    "Content-Type",  # Content type header
]

CORS_ALLOW_CREDENTIALS = True  # Allow credentials

if ENVIRONMENT == "dev":
    CORS_ALLOW_ALL_ORIGINS = True

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, 'templates')],  # Add template directories here
        "APP_DIRS": True,  # Enable app templates
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",  # Debug context processor
                "django.template.context_processors.request",  # Request context processor
                "django.contrib.auth.context_processors.auth",  # Auth context processor
                "django.contrib.messages.context_processors.messages",  # Messages context processor
                "django.template.context_processors.request",  # Request context processor
                'django.template.context_processors.static',  # Static context processor
            ],
        },
    },
]

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# Custom User Model
AUTH_USER_MODEL = "users.User"

# Load secret file if in production
# if ENVIRONMENT == "prod":
#     load_dotenv("/etc/secrets/env.prod")  # Load production secrets

# General settings
SECRET_KEY = os.getenv("SECRET_KEY")  # Secret key for Django
BASE_URL = os.getenv("BASE_URL")  # Base URL for the project
JWT_SECRET = os.getenv("JWT_SECRET")  # Secret key for JWT tokens

# Parse the DATABASE_URL environment variable
default_db_config = dj_database_url.config(
    default=os.getenv("DATABASE_URL"),  # Load from .env file or environment
    conn_max_age=600,  # Reuse connections for up to 600 seconds
    ssl_require=ENVIRONMENT == "prod",  # Enforce SSL in production
)

# Database configuration with explicit overrides
DATABASES = {
    "default": {
        **default_db_config,  # Base configuration parsed by dj_database_url
        "ENGINE": default_db_config.get("ENGINE", "django.db.backends.postgresql"),
        "NAME": default_db_config.get("NAME", os.getenv("DB_NAME")),
        "USER": default_db_config.get("USER", os.getenv("DB_USER")),
        "PASSWORD": default_db_config.get("PASSWORD", os.getenv("DB_PASSWORD")),
        "HOST": default_db_config.get("HOST", os.getenv("DB_HOST")),
        "PORT": default_db_config.get("PORT", os.getenv("DB_PORT")),
        "CONN_MAX_AGE": default_db_config.get("CONN_MAX_AGE", 600),
        "OPTIONS": {
            **default_db_config.get("OPTIONS", {}),  # Merge existing options
            "options": "-c search_path=public",  # Specify the default schema
        },
        "DISABLE_SERVER_SIDE_CURSORS": True,  # Optimize for specific queries
    }
}

# Enforce additional production-specific settings
if ENVIRONMENT == "prod":
    DATABASES["default"]["OPTIONS"].update({
        "sslmode": "require",  # Enforce SSL for secure connections
    })

REQUIRED_ENV_VARS = ["SECRET_KEY", "DATABASE_URL", "JWT_SECRET", "BASE_URL"]

for var in REQUIRED_ENV_VARS:
    if not os.getenv(var):
        raise ValueError(f"{var} is not set in environment variables.")

if ENVIRONMENT == "prod":
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_PRELOAD = True
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True

# if not DEBUG:  # Enable only in production
#     SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True") == "True"
#     SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
#     SECURE_HSTS_PRELOAD = os.getenv("SECURE_HSTS_PRELOAD", "True") == "True"
#     SECURE_HSTS_INCLUDE_SUBDOMAINS = (
#         os.getenv("SECURE_HSTS_INCLUDE_SUBDOMAINS", "True") == "True"
#     )
#     CSRF_COOKIE_SECURE = True
#     SESSION_COOKIE_SECURE = True

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",  # User attribute similarity validator
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",  # Minimum length validator
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",  # Common password validator
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",  # Numeric password validator
    },
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",  # For admin logins
    # "allauth.account.auth_backends.AuthenticationBackend",  # For allauth
]

# SOCIALACCOUNT_PROVIDERS = {
#     "google": {
#         "APP": {"client_id": "your-client-id", "secret": "your-secret", "key": ""}
#     }
# }

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",  # For session-based authentication
        'rest_framework.authentication.BasicAuthentication',
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",  # Default to authenticated users
        'rest_framework.permissions.AllowAny',  # Allow any user
    ),
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',    # Default renderer
        'rest_framework.renderers.BrowsableAPIRenderer',    # Browsable API renderer
        # 'drf_yasg.renderers.SwaggerJSONRenderer',   # Swagger JSON renderer
        # 'drf_yasg.renderers.OpenAPIRenderer',   # OpenAPI renderer
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        'anon': '60/minute',  # Anonymous users can make 60 requests per minute
        'user': '120/minute',  # Authenticated users can make 120 requests per minute
        'station_lookup': '10/second',  # For specific station lookup endpoints
        'route_planning': '30/minute',  # For route and trip planning APIs
        'ticket_booking': '15/minute',  # For ticket booking and QR code generation
    },
}

SIMPLE_JWT = {
    "SIGNING_KEY": os.getenv("JWT_SECRET"),  # Secret key for JWT tokens
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),  # Access token lifetime
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),  # Refresh token lifetime
}

# Create logs directory if it doesn't exist
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": str(LOGS_DIR / "debug.log"),
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],  # Only console for production
            "level": "INFO",
            "propagate": True,
        },
        "__main__": {
            "handlers": ["console"],  # Only console for production
            "level": "DEBUG",
            "propagate": True,
        },
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",  # Local memory cache
        "LOCATION": "unique-snowflake",
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"

INTERNAL_IPS = [
    "127.0.0.1",  # Localhost
]

HANDLER404 = "egypt_metro.views.custom_404"  # Custom 404 handler
HANDLER500 = "egypt_metro.views.custom_500"  # Custom 500 handler

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Swagger settings
SWAGGER_SETTINGS = {
    "USE_SESSION_AUTH": False,  # Disable session-based authentication for Swagger
    "SECURITY_DEFINITIONS": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
        },
    },
}

# Initialize Sentry for Error Tracking
# SENTRY_DSN = os.getenv("SENTRY_DSN")  # Use environment variable

# if SENTRY_DSN:
#     import sentry_sdk # type: ignore
#     from sentry_sdk.integrations.django import DjangoIntegration # type: ignore

#     sentry_sdk.init(
#         dsn=SENTRY_DSN,
#         integrations=[DjangoIntegration()],
#         send_default_pii=True,
#     )
# else:
#     print("Sentry DSN not configured. Skipping Sentry initialization.")

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "/static/"  # URL for static files

if os.getenv("RENDER"):
    STATIC_ROOT = "/opt/render/project/src/staticfiles/"
else:
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # Folder where static files will be collected

STATICFILES_STORAGE = (
    "whitenoise.storage.CompressedManifestStaticFilesStorage"  # Static files storage
)

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files (optional, if your project uses media uploads)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "mediafiles"  # Folder where media files will be uploaded

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"  # Default primary key field type
