"""Deployment settings for the isolated EatHub staging environment.

Set DJANGO_SETTINGS_MODULE=EatHub.settings_staging. This module deliberately
requires explicit secrets, database connectivity, host allowlists, and browser
origins rather than inheriting development defaults.
"""
import os
from urllib.parse import parse_qs, unquote, urlparse

from django.core.exceptions import ImproperlyConfigured

from .settings import *  # noqa: F403


def _required_env(name):
    value = os.environ.get(name, "").strip()
    if not value:
        raise ImproperlyConfigured(f"{name} must be configured for staging.")
    return value


def _csv_env(name):
    return [
        item.strip()
        for item in os.environ.get(name, "").split(",")
        if item.strip()
    ]


DEBUG = False
SECRET_KEY = _required_env("SECRET_KEY")

_render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
ALLOWED_HOSTS = sorted(set(_csv_env("ALLOWED_HOSTS") + ([_render_hostname] if _render_hostname else [])))
if not ALLOWED_HOSTS:
    raise ImproperlyConfigured(
        "Configure ALLOWED_HOSTS or deploy on Render with RENDER_EXTERNAL_HOSTNAME."
    )

CORS_ALLOWED_ORIGINS = _csv_env("CORS_ALLOWED_ORIGINS")
if not CORS_ALLOWED_ORIGINS:
    raise ImproperlyConfigured("CORS_ALLOWED_ORIGINS must contain the frontend origin.")

CSRF_TRUSTED_ORIGINS = _csv_env("CSRF_TRUSTED_ORIGINS")
if not CSRF_TRUSTED_ORIGINS:
    raise ImproperlyConfigured("CSRF_TRUSTED_ORIGINS must contain trusted HTTPS origins.")

_database_url = _required_env("DATABASE_URL")
_database = urlparse(_database_url)
if _database.scheme not in {"postgres", "postgresql"}:
    raise ImproperlyConfigured("Staging DATABASE_URL must use PostgreSQL.")

_database_name = unquote(_database.path.lstrip("/"))
_database_user = unquote(_database.username or "")
_database_password = unquote(_database.password or "")
_database_host = _database.hostname or ""
if not all((_database_name, _database_user, _database_password, _database_host)):
    raise ImproperlyConfigured("Staging DATABASE_URL is missing required connection fields.")

_database_query = parse_qs(_database.query)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _database_name,
        "USER": _database_user,
        "PASSWORD": _database_password,
        "HOST": _database_host,
        "PORT": str(_database.port or 5432),
        "CONN_MAX_AGE": 60,
        "OPTIONS": {
            "sslmode": _database_query.get("sslmode", ["require"])[0],
        },
    }
}

# Render terminates TLS at its proxy and forwards the original scheme.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"

MIDDLEWARE = [
    *MIDDLEWARE[:2],  # noqa: F405
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *MIDDLEWARE[2:],  # noqa: F405
]

# Neon Object Storage is S3-compatible and lives alongside the existing
# PostgreSQL project. Its public_read bucket serves images with DEBUG=False.
AWS_ACCESS_KEY_ID = _required_env("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = _required_env("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = _required_env("AWS_STORAGE_BUCKET_NAME")
AWS_S3_ENDPOINT_URL = _required_env("AWS_ENDPOINT_URL_S3")
AWS_S3_REGION_NAME = _required_env("AWS_REGION")
AWS_S3_ADDRESSING_STYLE = "path"
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_S3_URL_PROTOCOL = "https:"
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = False
AWS_S3_FILE_OVERWRITE = False
AWS_S3_OBJECT_PARAMETERS = {
    "CacheControl": "public, max-age=31536000, immutable",
}

STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
