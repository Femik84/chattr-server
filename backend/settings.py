from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# ====================================================
# 🔐 SECURITY & CLERK CONFIGURATION
# ====================================================

SECRET_KEY = 'django-insecure-@%dp+vlvcp7=$d#p%r6vl0m==@zbl%n64eam^ye)@cfoaf#$%s'

DEBUG = True

ALLOWED_HOSTS = ["*"]

CORS_ALLOW_ALL_ORIGINS = True

# Clerk API Keys (added directly)
# CLERK_SECRET_KEY = "sk_test_OVvWMbqw89J0CeF4PJvanPG2g2VIYIOZQ5NGr5CwQm"
# CLERK_PUBLISHABLE_KEY = "pk_test_bWFpbi1zdGFyZmlzaC0yNS5jbGVyay5hY2NvdW50cy5kZXYk"
# CLERK_JWKS_URL = "https://main-starfish-25.clerk.accounts.dev/.well-known/jwks.json"
# CLERK_ISSUER = "https://main-starfish-25.clerk.accounts.dev"
# CLERK_AUDIENCE = "mobile"


# ====================================================
# ⚙️ APPLICATION DEFINITION
# ====================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'corsheaders',

    # Local apps
    'users',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'backend.wsgi.application'


# ====================================================
# 🗄️ DATABASE
# ====================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ====================================================
# 🔒 PASSWORD VALIDATION
# ====================================================

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ====================================================
# 🌍 INTERNATIONALIZATION
# ====================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


AUTH_USER_MODEL = "users.CustomUser"


# ====================================================
# 🖼️ STATIC & MEDIA FILES
# ====================================================

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ====================================================
# 🧩 REST FRAMEWORK CONFIGURATION
# ====================================================

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}



# ====================================================
# 🆔 CUSTOM SETTINGS
# ====================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "femik84@gmail.com"
EMAIL_HOST_PASSWORD = "bkmhvrjutfkwfpog"  
DEFAULT_FROM_EMAIL = "noreply@yourdomain.com"
