from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# ====================================================
# 🔐 SECURITY
# ====================================================

SECRET_KEY = "django-insecure-@%dp+vlvcp7=$d#p%r6vl0m==@zbl%n64eam^ye)@cfoaf#$%s"
DEBUG = True
# With this (use your actual LAN IP)
ALLOWED_HOSTS = ['192.168.43.110', 'localhost', '127.0.0.1', "chattr-server-cukt.onrender.com", ".onrender.com",]

# Or add BASE_URL setting
BASE_URL = 'http://192.168.43.110:8000'

CORS_ALLOW_ALL_ORIGINS = True

# ====================================================
# ⚙️ APPLICATION DEFINITION
# ====================================================

INSTALLED_APPS = [
    # Channels / ASGI — MUST BE FIRST
    "daphne",
    "channels",

    # Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party apps
    "rest_framework",
    "corsheaders",

    # Local apps
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
# 🗄️ DATABASE
# ====================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# ====================================================
# 🔒 PASSWORD VALIDATION
# ====================================================

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ====================================================
# 🌍 INTERNATIONALIZATION
# ====================================================

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

AUTH_USER_MODEL = "users.CustomUser"

# ====================================================
# 🖼️ STATIC & MEDIA FILES
# ====================================================

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ====================================================
# 🧩 REST FRAMEWORK
# ====================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    )
}

# ====================================================
# 📡 CHANNEL LAYERS (Redis WebSocket backend)
# ====================================================
# Uncomment this later after installing Redis

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}

# ====================================================
# 🆔 DEFAULT SETTINGS
# ====================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ====================================================
# 📧 EMAIL SETTINGS
# ====================================================

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "femik84@gmail.com"
EMAIL_HOST_PASSWORD = "bkmhvrjutfkwfpog"
DEFAULT_FROM_EMAIL = "noreply@yourdomain.com"


from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=20),      
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),         
    "AUTH_HEADER_TYPES": ("Bearer",),
}