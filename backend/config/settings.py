"""Django settings for the Nexus backend.

Environment-driven configuration:
- SECRET_KEY, DEBUG, ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS, DATABASE_URL
- placeholders for future LLM keys (LLM_API_KEY, ...)
Real secrets live only in .env, which is ignored by Git.
"""
import os
from pathlib import Path
from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load local .env if it exists (never committed).
load_dotenv(BASE_DIR / ".env")


def _env_bool(name: str, default: str = "False") -> bool:
    """Read a boolean environment variable."""
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str, default: str = "") -> list[str]:
    """Read a comma-separated environment variable into a list."""
    raw = os.environ.get(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# --- Core -------------------------------------------------------------------
DEBUG = _env_bool("DEBUG", "True")

SECRET_KEY = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    if DEBUG:
        # Development-only fallback so the project runs without a .env file.
        SECRET_KEY = "insecure-development-key-do-not-use-in-production"
    else:
        raise ImproperlyConfigured("SECRET_KEY must be set when DEBUG is False.")

ALLOWED_HOSTS = _env_list("ALLOWED_HOSTS", "localhost,127.0.0.1")


# --- Database ---------------------------------------------------------------
def _database_config(url: str) -> dict:
    """Translate DATABASE_URL into a Django DATABASES entry.

    PostgreSQL is the production target; sqlite is used for local development
    when DATABASE_URL is unset or uses the sqlite scheme.
    """
    if not url:
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }

    parsed = urlparse(url)

    if parsed.scheme in ("postgres", "postgresql"):
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": parsed.path.lstrip("/") or "nexus",
            "USER": parsed.username or "",
            "PASSWORD": parsed.password or "",
            "HOST": parsed.hostname or "",
            "PORT": str(parsed.port or ""),
        }

    if parsed.scheme == "sqlite":
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": Path(parsed.path) if parsed.path else BASE_DIR / "db.sqlite3",
        }

    raise ImproperlyConfigured(f"Unsupported DATABASE_URL scheme: {parsed.scheme!r}")


DATABASES = {"default": _database_config(os.environ.get("DATABASE_URL", ""))}


# --- Applications -----------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third party
    "rest_framework",
    "corsheaders",
    # Local
    "chatbot.apps.ChatbotConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # CORS must run early so preflight requests are answered before anything else.
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Password validation (Django defaults)
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# --- CORS -------------------------------------------------------------------
# The React dev server is the only origin allowed to call the API locally.
CORS_ALLOWED_ORIGINS = _env_list(
    "CORS_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
)
# Future: allow credentials/extra headers explicitly if the API needs them.


# --- Django REST Framework --------------------------------------------------
REST_FRAMEWORK = {
    # Authentication and permissions will be added together with the first
    # protected endpoints; for now the API is read-only and open in DEBUG.
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
}


# --- Internationalization / static -----------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
