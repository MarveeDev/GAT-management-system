import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# Environment indicator. "development" is the safe default; set
# FLASK_ENV=production (or APP_ENV=production) to enable production validation.
ENVIRONMENTS = ("development", "testing", "production")


def resolve_environment() -> str:
    value = (os.getenv("FLASK_ENV") or os.getenv("APP_ENV") or "development").strip().lower()
    return value if value in ENVIRONMENTS else "development"


def _env_bool(name: str, default: bool = False) -> bool:
    """Parse a boolean environment variable into a real bool.

    Accepts common truthy spellings ("1", "true", "yes", "on") so callers never
    end up with the literal string "false" being treated as truthy.
    """
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name: str, default: str) -> list[str]:
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


# Development-only fallbacks. These are intentionally weak and must never be
# used in production (enforced by validate_production_config below).
_DEV_SECRET_KEY = "dev-only-secret-key-change-me"
_DEV_JWT_SECRET_KEY = "dev-only-jwt-secret-key-change-me"

# Values that are obviously not production-safe secrets.
_INSECURE_SECRET_VALUES = {
    "",
    _DEV_SECRET_KEY,
    _DEV_JWT_SECRET_KEY,
    "dev-only-change-me",
    "dev-only-jwt-secret-change-me",
    "change-me",
    "change-me-to-a-long-random-string",
    "replace-with-a-strong-secret",
    "secret",
    "changeme",
    "password",
}

_MIN_SECRET_LENGTH = 16


class Config:
    APP_ENV = resolve_environment()

    SECRET_KEY = os.getenv("SECRET_KEY", _DEV_SECRET_KEY)
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", _DEV_JWT_SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.getenv("JWT_ACCESS_TOKEN_HOURS", "12"))
    )

    CORS_ORIGINS = _env_list("CORS_ORIGINS", "http://localhost:5173")

    # Debug defaults to off. It may be enabled explicitly in development via
    # FLASK_DEBUG=1, but is always forced off in production.
    DEBUG = _env_bool("FLASK_DEBUG", default=False) and APP_ENV != "production"

    DATABASE_URL = os.getenv("DATABASE_URL", "")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL or (
        f"sqlite:///{os.path.join(BASE_DIR, 'dev.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SMS provider (mock by default; never sends real SMS)
    SMS_PROVIDER = os.getenv("SMS_PROVIDER", "mock")
    SMS_API_KEY = os.getenv("SMS_API_KEY", "")
    SMS_SENDER_ID = os.getenv("SMS_SENDER_ID", "")
    SMS_MOCK_FAIL = _env_bool("SMS_MOCK_FAIL", default=False)

    # A PENDING SMS record must be at least this old (seconds) before it may
    # be resolved as "outcome unknown". Prevents racing an in-flight send.
    SMS_PENDING_RECOVERY_SECONDS = _env_int("SMS_PENDING_RECOVERY_SECONDS", 60)

    # Login rate limiting (in-process; per (ip, email) and per ip).
    LOGIN_RATE_LIMIT_MAX_ATTEMPTS = _env_int("LOGIN_RATE_LIMIT_MAX_ATTEMPTS", 5)
    LOGIN_RATE_LIMIT_IP_MAX_ATTEMPTS = _env_int(
        "LOGIN_RATE_LIMIT_IP_MAX_ATTEMPTS", 25
    )
    LOGIN_RATE_LIMIT_WINDOW_SECONDS = _env_int(
        "LOGIN_RATE_LIMIT_WINDOW_SECONDS", 300
    )


def validate_production_config(config) -> None:
    """Fail fast when a production config is missing required values.

    Raises RuntimeError naming the missing/insecure variable, never the value.
    """
    missing = []
    for name in ("SECRET_KEY", "JWT_SECRET_KEY", "DATABASE_URL"):
        if not config.get(name):
            missing.append(name)
    if missing:
        raise RuntimeError(
            "Production configuration error: missing required variable(s): "
            + ", ".join(missing)
            + "."
        )

    for name in ("SECRET_KEY", "JWT_SECRET_KEY"):
        value = config.get(name) or ""
        if value in _INSECURE_SECRET_VALUES or len(value) < _MIN_SECRET_LENGTH:
            raise RuntimeError(
                f"Production configuration error: {name} is missing or insecure."
            )
