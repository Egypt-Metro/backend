"""
Django settings for metro project.

Generated by 'django-admin startproject' using Django 5.1.3.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

import os  # Operating system dependent functionality

# from decouple import config  # Configuration helper
from datetime import datetime  # Date and time utilities
from datetime import timedelta  # Time delta for JWT tokens

# import logging
from pathlib import Path  # File path helper

import dj_database_url  # type: ignore # Parse database URLs
from corsheaders.defaults import default_headers  # Default headers for CORS
from dotenv import load_dotenv  # Load environment variables from .env file

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent  # Base directory for the project
PROJECT_NAME = "Egypt Metro"

# Load the appropriate .env file based on an environment variable
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")  # Default to dev
dotenv_path = BASE_DIR / f"env/.env.{ENVIRONMENT}"
load_dotenv(dotenv_path)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY")  # Secret key for Django
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")   # Environment (dev, test, prod)
DEBUG = ENVIRONMENT == "dev"  # Debug mode based on environment
BASE_URL = os.getenv("BASE_URL")  # Base URL for the project
JWT_SECRET = os.getenv("JWT_SECRET")  # Secret key for JWT tokens

# Set API start time to the application's boot time
API_START_TIME = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",  # Admin panel
    "django.contrib.auth",  # Authentication framework
    'django_rest_passwordreset',  # Password reset
    "django.contrib.contenttypes",  # Content types framework
    "django.contrib.sessions",  # Sessions framework
    "django.contrib.messages",  # Messages framework
    "django.contrib.staticfiles",  # Static files
    # External packages
    "allauth",  # Authentication
    "allauth.account",  # Account management
    # "allauth.socialaccount",  # Social authentication
    # "allauth.socialaccount.providers.google",  # Google OAuth provider
    "rest_framework",  # REST framework
    "rest_framework_simplejwt",  # JWT authentication
    "corsheaders",  # CORS headers
    "drf_yasg",  # Swagger
    "constance",  # Dynamic settings
    "constance.backends.database",  # Database backend for Constance
    "channels",  # Channels
    "import_export",  # Import and export data
    "rangefilter",  # Range filter for Django admin
    'sslserver',    # SSL server for development
    'django_extensions',  # Django extensions
    # Custom apps
    "apps.users.apps.UsersConfig",  # Users app
    "apps.stations.apps.StationsConfig",  # Stations app
    "apps.routes.apps.RoutesConfig",  # Routes app
    "apps.trains.apps.TrainsConfig",  # Trains app
    "apps.authentication.apps.AuthenticationConfig",
]

# Middleware configuration
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",  # Security middleware
    "whitenoise.middleware.WhiteNoiseMiddleware",  # WhiteNoise middleware
    "django.contrib.sessions.middleware.SessionMiddleware",  # Session middleware
    "django.middleware.common.CommonMiddleware",  # Common middleware
    "django.middleware.csrf.CsrfViewMiddleware",  # CSRF middleware
    "django.contrib.auth.middleware.AuthenticationMiddleware",  # Authentication middleware
    "django.contrib.messages.middleware.MessageMiddleware",  # Messages middleware
    "django.middleware.clickjacking.XFrameOptionsMiddleware",  # Clickjacking middleware
    "corsheaders.middleware.CorsMiddleware",  # CORS middleware
    "allauth.account.middleware.AccountMiddleware",  # Account middleware
]

ROOT_URLCONF = "metro.urls"  # Root URL configuration
WSGI_APPLICATION = "metro.wsgi.application"  # WSGI application

# AI Model Settings
AI_MODEL_PATH = "path/to/your/trained/model"
AI_MODEL_CONFIDENCE_THRESHOLD = 0.8

# AI Service Configuration
AI_SERVICE_URL = "http://your-ai-service-url/api"  # Your friend's AI service URL
AI_SERVICE_API_KEY = "your-api-key"  # API key for authentication
AI_SERVICE_TIMEOUT = 30  # seconds

# Email Configuration (Production-focused with Mailgun)
EMAIL_BACKEND = 'anymail.backends.mailgun.EmailBackend'
ANYMAIL = {
    "MAILGUN_API_KEY": os.getenv("MAILGUN_API_KEY"),
    "MAILGUN_SENDER_DOMAIN": os.getenv("MAILGUN_DOMAIN"),
    "MAILGUN_API_URL": "https://api.eu.mailgun.net/v3",  # Use EU endpoint if in Europe
}

# Email settings
DEFAULT_FROM_EMAIL = f"Metro App <noreply@{os.getenv('MAILGUN_DOMAIN')}>"
EMAIL_TIMEOUT = 30
EMAIL_SUBJECT_PREFIX = '[Metro] '

# Password Reset Settings
DJANGO_REST_PASSWORDRESET_TOKEN_CONFIG = {
    "CLASS": "django_rest_passwordreset.tokens.RandomStringTokenGenerator",
    "OPTIONS": {
        "min_length": 20,
        "max_length": 30
    }
}
DJANGO_REST_PASSWORDRESET_NO_INFORMATION_LEAKAGE = True
DJANGO_REST_MULTITOKENAUTH_RESET_TOKEN_EXPIRY_TIME = 24  # Hours

# Define REQUIRED_ENV_VARS and add to it
REQUIRED_ENV_VARS = ["MAILGUN_API_KEY", "MAILGUN_DOMAIN"]

# For production Redis
# if ENVIRONMENT == 'prod':
#     REDIS_HOST = os.getenv('REDIS_HOST', 'your-production-redis-host')
#     REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
# else:
#     REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
#     REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

# Security Settings based on environment
if ENVIRONMENT == 'prod':
    # Production settings
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
else:
    # Development settings
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_PROXY_SSL_HEADER = None

# Update ALLOWED_HOSTS and CORS settings
ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "backend-54v5.onrender.com",
]

CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "https://backend-54v5.onrender.com",
] if ENVIRONMENT == "prod" else [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
]

# Add development URLs to CSRF trusted origins
CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://localhost:3000",
    "https://backend-54v5.onrender.com",
]

# CORS settings
CORS_ALLOW_HEADERS = list(default_headers) + [
    "Authorization",  # Authorization header
    "Content-Type",  # Content type header
]
CORS_ALLOW_CREDENTIALS = True  # Allow credentials

# if ENVIRONMENT == "dev":
#     INSTALLED_APPS += [
#         "silk",
#         "debug_toolbar",
#     ]
#     MIDDLEWARE += [
#         "silk.middleware.SilkyMiddleware",
#         "debug_toolbar.middleware.DebugToolbarMiddleware",
#     ]

#     INTERNAL_IPS = [
#         "127.0.0.1",  # Localhost
#         "localhost",   # Localhost
#         "0.0.0.0",     # Docker/Container or VM access
#     ]

#     SILKY_PYTHON_PROFILER = True  # Enables Python code profiling
#     SILKY_MAX_REQUESTS = 1000     # Limit the number of requests to profile
#     SILKY_RECORD_SQL = True       # Records SQL queries
#     SILKY_AUTHENTICATION = True   # Protect Silk interface with authentication

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],  # Add template directories here
        "APP_DIRS": True,  # Enable app templates
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",  # Debug context processor
                "django.template.context_processors.request",  # Request context processor
                "django.contrib.auth.context_processors.auth",  # Auth context processor
                "django.contrib.messages.context_processors.messages",  # Messages context processor
                "django.template.context_processors.static",  # Static context processor
                "metro.context_processors.project_name",
            ],
        },
    },
]

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

# Custom User Model
AUTH_USER_MODEL = "users.User"

# Add ASGI application
ASGI_APPLICATION = "config.asgi.application"

# Add Channel Layers configuration
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [(os.getenv("REDIS_HOST", "127.0.0.1"), 6379)],
        },
    },
}

# API Documentation
SPECTACULAR_SETTINGS = {
    "TITLE": "Metro API",
    "DESCRIPTION": "API documentation for Metro Train System",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# Parse the DATABASE_URL environment variable
default_db_config = dj_database_url.config(
    default=os.getenv("DATABASE_URL"),  # Load from .env file or environment
    conn_max_age=600,  # Reuse connections for up to 600 seconds
    ssl_require=ENVIRONMENT == "prod",  # Enforce SSL in production
)

# Database configuration with explicit overrides
# if os.getenv("ENVIRONMENT") == "prod":
DATABASES = {
    "default": {
        **default_db_config,  # Base configuration parsed by dj_database_url
        "ENGINE": default_db_config.get("ENGINE", "django.db.backends.postgresql"),
        "NAME": default_db_config.get("NAME", os.getenv("DB_NAME")),
        "USER": default_db_config.get("USER", os.getenv("DB_USER")),
        "PASSWORD": default_db_config.get("PASSWORD", os.getenv("DB_PASSWORD")),
        "HOST": default_db_config.get("HOST", os.getenv("DB_HOST")),
        "PORT": default_db_config.get("PORT", os.getenv("DB_PORT")),
        "CONN_MAX_AGE": default_db_config.get("CONN_MAX_AGE", 0),  # Reuse connections up to 600 sec
        "OPTIONS": {
            **default_db_config.get("OPTIONS", {}),  # Merge existing options
            "options": "-c search_path=public",  # Specify the default schema
            "connect_timeout": 30,  # Increase the connection timeout (in seconds)
            "keepalives": 1,  # Enable TCP keepalives
            "keepalives_idle": 60,  # Increase this value
            "keepalives_interval": 10,
            "keepalives_count": 5,
        },
        "DISABLE_SERVER_SIDE_CURSORS": True,  # Optimize for specific queries
    }
}
# else:  # Use SQLite for local development
#     DATABASES = {
#         "default": {
#             "ENGINE": "django.db.backends.sqlite3",
#             "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
#         }
#     }

# Enforce additional production-specific settings
if ENVIRONMENT == "prod":
    DATABASES["default"]["OPTIONS"].update(
        {
            "sslmode": "require",  # Enforce SSL for secure connections
        }
    )
    # Security settings Production
    CSRF_COOKIE_SECURE = True  # Ensure CSRF cookies are only sent over HTTPS
    SESSION_COOKIE_SECURE = True  # Ensure session cookies are only sent over HTTPS
    SECURE_BROWSER_XSS_FILTER = True    # Enable XSS protection for browsers
    SECURE_CONTENT_TYPE_NOSNIFF = True  # Prevent content type sniffing
    SECURE_HSTS_SECONDS = 31536000  # 1 year in seconds
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True   # Include subdomains for HSTS
    SECURE_HSTS_PRELOAD = True  # Enable HSTS preload list
    SECURE_SSL_REDIRECT = True  # Redirect HTTP to HTTPS

    # Proxy Settings
    USE_X_FORWARDED_HOST = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_REFERRER_POLICY = "same-origin"  # Referrer policy
    X_FRAME_OPTIONS = "DENY"    # Prevent framing of site content

REQUIRED_ENV_VARS = ["SECRET_KEY", "DATABASE_URL", "JWT_SECRET", "BASE_URL"]

for var in REQUIRED_ENV_VARS:
    if not os.getenv(var):
        raise ValueError(f"{var} is not set in environment variables.")

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        # User attribute similarity validator
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        # Minimum length validator
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
        # Common password validator
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
        # Numeric password validator
    },
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",  # For admin logins
    # "allauth.account.auth_backends.AuthenticationBackend",  # For allauth
]

REST_FRAMEWORK = {
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",  # For session-based authentication
        "rest_framework.authentication.BasicAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",  # Default to authenticated users
        "rest_framework.permissions.AllowAny",  # Allow any user
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",  # Default renderer
        "rest_framework.renderers.BrowsableAPIRenderer",  # Browsable API renderer
        # 'drf_yasg.renderers.SwaggerJSONRenderer',   # Swagger JSON renderer
        # 'drf_yasg.renderers.OpenAPIRenderer',   # OpenAPI renderer
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        'anon': '100/day',
        'user': '1000/day',
        "station_lookup": "10/second",  # For specific station lookup endpoints
        "route_planning": "30/minute",  # For route and trip planning APIs
        "ticket_booking": "15/minute",  # For ticket booking and QR code generation
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SIMPLE_JWT = {
    "SIGNING_KEY": os.getenv("JWT_SECRET"),  # Secret key for JWT tokens
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),  # Access token lifetime   # 1 hour
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),  # Refresh token lifetime  # 7 days
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
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "logs/debug.log",
            "formatter": "verbose",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "apps.stations": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": True,
        },
        "apps.routes": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": True,
        },
    },
}

# Add Cache configuration
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': f"redis://{os.getenv('REDIS_HOST', '127.0.0.1')}:6379/1",
#         'OPTIONS': {
#             'CLIENT_CLASS': 'django_redis.client.DefaultClient',
#             'PARSER_CLASS': 'redis.connection.HiredisParser',
#             'SOCKET_TIMEOUT': 5,
#             'SOCKET_CONNECT_TIMEOUT': 5,
#             'CONNECTION_POOL_CLASS': 'redis.connection.BlockingConnectionPool',
#             'CONNECTION_POOL_CLASS_KWARGS': {
#                 'max_connections': 50,
#                 'timeout': 20,
#             },
#             'MAX_CONNECTIONS': 1000,
#             'RETRY_ON_TIMEOUT': True,
#         },
#     }
# }

# Cache time to live is 15 minutes
CACHE_TTL = 60 * 15

# Cache configuration
if ENVIRONMENT == "prod":
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": os.getenv("CACHE_LOCATION", "my_cache_table"),
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": os.getenv("CACHE_BACKEND", "django.core.cache.backends.locmem.LocMemCache"),
            "LOCATION": os.getenv("CACHE_LOCATION", "unique-snowflake"),
        }
    }

# Constance Settings
CONSTANCE_BACKEND = "constance.backends.database.DatabaseBackend"
CONSTANCE_CONFIG = {
    "SITE_TITLE": ("Egypt Metro", "Site title displayed in the admin panel."),
    "DEFAULT_TIMEOUT": (30, "Default timeout for user actions."),
}

# Session Configuration
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"  # Cached database session engine
SESSION_CACHE_ALIAS = "default"  # Cache alias for sessions
SESSION_COOKIE_AGE = 3600  # Session cookie age in seconds (1 hour)
SESSION_EXPIRE_AT_BROWSER_CLOSE = ENVIRONMENT == "dev"  # True for development, False for production
SESSION_SAVE_EVERY_REQUEST = True  # Save session data on every request

HANDLER404 = "metro.views.custom_404"  # Custom 404 handler
HANDLER500 = "metro.views.custom_500"  # Custom 500 handler

# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "/static/"  # URL for static files

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")  # Folder where static files will be collected

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"  # Static files storage

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# Media files (optional, if your project uses media uploads)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "mediafiles"  # Folder where media files will be uploaded

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"  # Default primary key field type
