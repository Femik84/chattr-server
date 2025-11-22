from pathlib import Path
from datetime import timedelta
import cloudinary

# ====================================================
# BASE DIRECTORY
# ====================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# ====================================================
# SECURITY
# ====================================================
SECRET_KEY = "django-insecure-@%dp+vlvcp7=$d#p%r6vl0m==@zbl%n64eam^ye)@cfoaf#$%s"
DEBUG = True
ALLOWED_HOSTS = [
    '192.168.43.110',
    'localhost',
    '127.0.0.1',
    "chattr-server-cukt.onrender.com",
    ".onrender.com",
]

CORS_ALLOW_ALL_ORIGINS = True

# ====================================================
# APPLICATIONS
# ====================================================
INSTALLED_APPS = [
    # Channels
    "daphne",
    "channels",

    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "cloudinary",
    "cloudinary_storage",
    "rest_framework",
    "corsheaders",

    # Local
    "users",
    "posts",
    "comments",
    "notifications",
    "messaging",
    "search",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "backend.middleware.active_user_middleware.ActiveUserMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "backend.wsgi.application"
ASGI_APPLICATION = "backend.asgi.application"

# ====================================================
# DATABASE
# ====================================================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ====================================================
# PASSWORD VALIDATORS
# ====================================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ====================================================
# INTERNATIONALIZATION
# ====================================================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
AUTH_USER_MODEL = "users.CustomUser"

# ====================================================
# STATIC & MEDIA FILES
# ====================================================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    # Media (uploads)
    "default": {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    },

    # Static files
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# ====================================================
# CLOUDINARY CONFIG
# ====================================================
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": "dhazpsb4d",
    "API_KEY": "121798156135788",
    "API_SECRET": "alTPWNg_EGaxG2-8gRk0gYQqYVs",
}

cloudinary.config(
    cloud_name=CLOUDINARY_STORAGE["CLOUD_NAME"],
    api_key=CLOUDINARY_STORAGE["API_KEY"],
    api_secret=CLOUDINARY_STORAGE["API_SECRET"],
    secure=True,
)

# ====================================================
# REST FRAMEWORK
# ====================================================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    )
}

# ====================================================
# CHANNEL LAYERS
# ====================================================
# CHANNEL_LAYERS = {
#     "default": {
#         "BACKEND": "channels_redis.core.RedisChannelLayer",
#         "CONFIG": {
#             "hosts": [("127.0.0.1", 6379)],
#         },
#     },
# }



# ====================================================
# 📡 CHANNEL LAYERS (Upstash Redis)
# ====================================================
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [
                # Hardcoded Upstash Redis URL with TLS
                "rediss://default:AYNEAAIncDI3MGRmZTY0Y2RiZWY0OTA4YTg1ZDJlNzA2ZGI0YTk0NHAyMzM2MDQ@liberal-chipmunk-33604.upstash.io:6379"
            ],
        },
    },
}

# ====================================================
# EMAIL SETTINGS
# ====================================================
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "femik84@gmail.com"
EMAIL_HOST_PASSWORD = "bkmhvrjutfkwfpog"
DEFAULT_FROM_EMAIL = "noreply@yourdomain.com"

# ====================================================
# SIMPLE JWT
# ====================================================
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=20),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
