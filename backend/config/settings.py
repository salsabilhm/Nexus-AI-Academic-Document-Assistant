"""Django settings for the Nexus backend.

Environment-driven configuration:
- SECRET_KEY, DEBUG, ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS, DATABASE_URL
- placeholders for future LLM keys (LLM_API_KEY, ...)
Real secrets live only in .env, which is ignored by Git.
"""
import os
from pathlib import Path
from urllib.parse import urlparse, unquote

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

    PostgreSQL (Supabase) is the only supported production backend.
    SQLite is accepted locally when DATABASE_URL is unset or uses sqlite://.

    For Supabase's transaction-mode pooler (port 6543) we disable
    server-side cursors and named prepared statements, which pgbouncer does
    not support in transaction mode.
    """
    if not url:
        if not DEBUG:
            raise ImproperlyConfigured(
                "DATABASE_URL must be set when DEBUG is False."
            )
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }

    # --- scheme check (safe: scheme never contains special chars) -----------
    if "://" not in url:
        raise ImproperlyConfigured("DATABASE_URL must include a scheme (e.g. postgresql://...)")
    scheme, rest = url.split("://", 1)

    if scheme in ("postgres", "postgresql"):
        # Split on the LAST '@' so passwords containing '@' are handled safely.
        at_idx = rest.rfind("@")
        if at_idx == -1:
            raise ImproperlyConfigured("DATABASE_URL is missing the '@' host separator.")
        userinfo = rest[:at_idx]       # user:password (may contain special chars)
        hostinfo = rest[at_idx + 1:]   # host:port/dbname  (no password here)

        # Strip any stray leading/trailing bracket that can corrupt IPv4 parsing.
        hostinfo = hostinfo.strip("[]")

        # Parse user and percent-encoded password.
        if ":" in userinfo:
            user, pw_encoded = userinfo.split(":", 1)
        else:
            user, pw_encoded = userinfo, ""
        password = unquote(pw_encoded)   # decode %5B → [ etc.

        # Parse host, port, dbname from the safe (no-password) tail.
        parsed_tail = urlparse(f"postgresql://{hostinfo}")
        host   = parsed_tail.hostname or ""
        port   = str(parsed_tail.port or "5432")
        dbname = parsed_tail.path.lstrip("/") or "postgres"

        is_pooler = port == "6543"
        config: dict = {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": dbname,
            "USER": user,
            "PASSWORD": password,
            "HOST": host,
            "PORT": port,
            "OPTIONS": {
                # psycopg v3 — require TLS for all remote Supabase connections.
                "sslmode": "require",
            },
        }
        if is_pooler:
            # pgbouncer transaction mode does not support named cursors/prepared stmts.
            config["DISABLE_SERVER_SIDE_CURSORS"] = True
            config["OPTIONS"]["prepare_threshold"] = None  # type: ignore[index]
        return config

    if scheme == "sqlite":
        # urlparse is safe here — sqlite URLs never contain passwords.
        parsed_sqlite = urlparse(url)
        return {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": Path(parsed_sqlite.path) if parsed_sqlite.path else BASE_DIR / "db.sqlite3",
        }

    raise ImproperlyConfigured(f"Unsupported DATABASE_URL scheme: {scheme!r}")


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
# Only local origins on the React dev server may call the API.
# Vite silently moves to the next free port (5174, ...) when 5173 is already
# taken, so every local dev origin must be listed here: an origin that is not
# listed gets no Access-Control-Allow-Origin header and the browser reports a
# "Network Error" even though Django answered the request successfully.
CORS_ALLOWED_ORIGINS = _env_list(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:5174,"
    "http://127.0.0.1:5173,http://127.0.0.1:5174",
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


# --- Supabase Storage -------------------------------------------------------
# Used by chatbot/services/storage.py to upload PDF files.
# All three values must be set when DEBUG is False.
SUPABASE_URL: str = os.environ.get("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY: str = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_STORAGE_BUCKET: str = os.environ.get("SUPABASE_STORAGE_BUCKET", "documents")

if not DEBUG:
    if not SUPABASE_URL:
        raise ImproperlyConfigured("SUPABASE_URL must be set when DEBUG is False.")
    if not SUPABASE_SERVICE_ROLE_KEY:
        raise ImproperlyConfigured("SUPABASE_SERVICE_ROLE_KEY must be set when DEBUG is False.")


# --- Future AI services (placeholders) -------------------------------------
# These are not used yet; they will be wired up in later phases.
LLM_API_KEY: str = os.environ.get("LLM_API_KEY", "")
LLM_MODEL: str = os.environ.get("LLM_MODEL", "")
EMBEDDING_API_KEY: str = os.environ.get("EMBEDDING_API_KEY", "")
