"""
Django settings for JIO project.
Desarrollo: SQLite, media local.
Producción (Render): PostgreSQL, Cloudinary para imágenes, WhiteNoise para estáticos.
"""

from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Seguridad: variables de entorno en producción
SECRET_KEY = os.environ.get(
    "SECRET_KEY",
    "django-insecure-cambiar-en-produccion",
)
DEBUG = os.environ.get("DEBUG", "True").lower() in ("1", "true", "yes")
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    ".onrender.com",
]
if os.environ.get("ALLOWED_HOSTS"):
    ALLOWED_HOSTS.extend(h.strip() for h in os.environ["ALLOWED_HOSTS"].split(",") if h.strip())

# Cloudinary (solo para MEDIA).
# Se activa solo si existe CLOUDINARY_URL (recomendado) o si están las 3 variables separadas.
USE_CLOUDINARY = bool(os.environ.get("CLOUDINARY_URL")) or all(
    os.environ.get(k) for k in ("CLOUDINARY_CLOUD_NAME", "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET")
)
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "FiestaEntreOso_app.apps.FiestaEntreOsoAppConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "JIO.urls"
WSGI_APPLICATION = "JIO.wsgi.application"

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

# Base de datos: PostgreSQL en Render (DATABASE_URL), SQLite en local
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
if os.environ.get("DATABASE_URL"):
    import dj_database_url
    DATABASES["default"] = dj_database_url.config(
        conn_max_age=600,
        conn_health_checks=True,
    )

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

# Estáticos: WhiteNoise (collectstatic → staticfiles)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "FiestaEntreOso_app" / "static",
]
# Render: modo básico y robusto (sin compresión/manifest) para evitar FileNotFoundError
STATICFILES_STORAGE = "whitenoise.storage.StaticFilesStorage"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.StaticFilesStorage",
    },
}

# Media: Cloudinary si hay credenciales, sino carpeta local
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

if USE_CLOUDINARY:
    CLOUDINARY_STORAGE = {
        "CLOUD_NAME": os.environ.get("CLOUDINARY_CLOUD_NAME", ""),
        "API_KEY": os.environ.get("CLOUDINARY_API_KEY", ""),
        "API_SECRET": os.environ.get("CLOUDINARY_API_SECRET", ""),
    }
    if os.environ.get("CLOUDINARY_URL"):
        import re
        m = re.match(r"cloudinary://([^:]+):([^@]+)@([^/]+)", os.environ["CLOUDINARY_URL"])
        if m:
            CLOUDINARY_STORAGE["API_KEY"] = m.group(1)
            CLOUDINARY_STORAGE["API_SECRET"] = m.group(2)
            CLOUDINARY_STORAGE["CLOUD_NAME"] = m.group(3)
    STORAGES["default"] = {
        "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
    }
else:
    STORAGES["default"] = {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
