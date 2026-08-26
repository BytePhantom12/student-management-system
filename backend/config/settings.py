import os
import sys
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR.parent / ".env")
IS_TESTING = "test" in sys.argv
SECRET_KEY = os.getenv("SECRET_KEY", "unsafe-development-key-change-me")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ALLOWED_HOSTS = [x.strip() for x in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if x.strip()]
INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "corsheaders", "rest_framework", "rest_framework_simplejwt.token_blacklist", "django_filters", "drf_spectacular",
    "accounts", "teachers", "students", "hifz", "attendance", "audit", "dashboard",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware", "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware", "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware", "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware", "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "APP_DIRS": True,
              "OPTIONS": {"context_processors": ["django.template.context_processors.request", "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION = "config.wsgi.application"
def required_env(name):
    value = os.getenv(name)
    if not value:
        raise ImproperlyConfigured(f"Required environment variable {name} is not set.")
    return value

if IS_TESTING:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "test.sqlite3"}}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": required_env("DB_NAME"),
            "USER": required_env("DB_USER"),
            "PASSWORD": required_env("DB_PASSWORD"),
            "HOST": required_env("DB_HOST"),
            "PORT": required_env("DB_PORT"),
            "OPTIONS": {"charset": "utf8mb4"},
        }
    }
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
AUTH_USER_MODEL = "accounts.User"
LANGUAGE_CODE, TIME_ZONE, USE_I18N, USE_TZ = "en-us", "Asia/Kuala_Lumpur", True, True
STATIC_URL, STATIC_ROOT = "static/", BASE_DIR / "staticfiles"
MEDIA_URL, MEDIA_ROOT = "/media/", BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CORS_ALLOWED_ORIGINS = [x.strip() for x in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",") if x.strip()]
BLOB_READ_WRITE_TOKEN = os.getenv("BLOB_READ_WRITE_TOKEN", "")
BLOB_REQUEST_TIMEOUT_SECONDS = float(os.getenv("BLOB_REQUEST_TIMEOUT_SECONDS", "15"))
PROFILE_IMAGE_MAX_BYTES = int(os.getenv("PROFILE_IMAGE_MAX_BYTES", str(3 * 1024 * 1024)))
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ("rest_framework_simplejwt.authentication.JWTAuthentication",),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination", "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": ("django_filters.rest_framework.DjangoFilterBackend", "rest_framework.filters.SearchFilter", "rest_framework.filters.OrderingFilter"),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "config.exceptions.api_exception_handler",
}
SIMPLE_JWT = {"ACCESS_TOKEN_LIFETIME": timedelta(minutes=int(os.getenv("ACCESS_TOKEN_MINUTES", "15"))), "REFRESH_TOKEN_LIFETIME": timedelta(days=int(os.getenv("REFRESH_TOKEN_DAYS", "7"))), "ROTATE_REFRESH_TOKENS": True, "BLACKLIST_AFTER_ROTATION": True}
SPECTACULAR_SETTINGS = {"TITLE": "Quran Institution Student Management API", "VERSION": "1.0.0", "SERVE_INCLUDE_SCHEMA": False}
if not DEBUG and not IS_TESTING:
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "True").lower() == "true"
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
    SECURE_HSTS_PRELOAD = SECURE_HSTS_SECONDS > 0
