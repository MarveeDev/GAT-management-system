import pytest

from app import create_app
from app.config import (
    Config,
    _DEV_JWT_SECRET_KEY,
    _DEV_SECRET_KEY,
    _INSECURE_SECRET_VALUES,
    _env_bool,
    _normalize_database_url,
    validate_production_config,
)


def _production_data(**overrides):
    data = {
        "SECRET_KEY": "super-secret-session-key-1234567890",
        "JWT_SECRET_KEY": "super-secret-jwt-key-1234567890",
        "DATABASE_URL": "postgresql+psycopg://user:pass@host:5432/db",
    }
    data.update(overrides)
    return data


class ProductionConfig:
    APP_ENV = "production"
    SECRET_KEY = "super-secret-session-key-1234567890"
    JWT_SECRET_KEY = "super-secret-jwt-key-1234567890"
    DATABASE_URL = "postgresql+psycopg://user:pass@host:5432/db"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    CORS_ORIGINS = ["http://localhost:5173"]


# --- development configuration --------------------------------------------


def test_development_environment_is_default():
    assert Config.APP_ENV == "development"


def test_development_defaults_are_clearly_dev_only():
    assert "dev-only" in _DEV_SECRET_KEY
    assert "dev-only" in _DEV_JWT_SECRET_KEY


def test_development_defaults_are_rejected_in_production():
    with pytest.raises(RuntimeError):
        validate_production_config(
            {
                "SECRET_KEY": _DEV_SECRET_KEY,
                "JWT_SECRET_KEY": _DEV_JWT_SECRET_KEY,
                "DATABASE_URL": "postgresql+psycopg://user:pass@host:5432/db",
            }
        )


def test_development_database_falls_back_to_sqlite():
    assert Config.SQLALCHEMY_DATABASE_URI.startswith("sqlite:///")


# --- PostgreSQL URL normalization ------------------------------------------


def test_postgres_scheme_normalized_to_psycopg():
    assert (
        _normalize_database_url("postgres://user:pass@host:5432/db")
        == "postgresql+psycopg://user:pass@host:5432/db"
    )


def test_postgresql_scheme_normalized_to_psycopg():
    assert (
        _normalize_database_url("postgresql://user:pass@host:5432/db")
        == "postgresql+psycopg://user:pass@host:5432/db"
    )


def test_postgresql_psycopg_scheme_left_unchanged():
    url = "postgresql+psycopg://user:pass@host:5432/db"
    assert _normalize_database_url(url) == url


def test_normalization_preserves_url_components():
    url = "postgresql://user:pass@host:5432/dbname?sslmode=require&application_name=gat"
    assert _normalize_database_url(url) == (
        "postgresql+psycopg://user:pass@host:5432/dbname"
        "?sslmode=require&application_name=gat"
    )


def test_normalization_preserves_postgres_scheme_components():
    url = "postgres://user:p%40ss@host:5432/dbname?sslmode=require"
    assert _normalize_database_url(url) == (
        "postgresql+psycopg://user:p%40ss@host:5432/dbname?sslmode=require"
    )


def test_non_postgres_schemes_are_unchanged():
    assert _normalize_database_url("sqlite:///app.db") == "sqlite:///app.db"
    assert (
        _normalize_database_url("mysql://user:pass@host:3306/db")
        == "mysql://user:pass@host:3306/db"
    )


def test_empty_database_url_is_unchanged():
    assert _normalize_database_url("") == ""


# --- boolean parsing ------------------------------------------------------


def test_env_bool_returns_real_boolean(monkeypatch):
    monkeypatch.delenv("FLASK_DEBUG", raising=False)
    assert _env_bool("FLASK_DEBUG", default=False) is False

    monkeypatch.setenv("FLASK_DEBUG", "1")
    assert _env_bool("FLASK_DEBUG", default=False) is True

    monkeypatch.setenv("FLASK_DEBUG", "false")
    assert _env_bool("FLASK_DEBUG", default=False) is False

    monkeypatch.setenv("FLASK_DEBUG", "0")
    assert _env_bool("FLASK_DEBUG", default=False) is False

    monkeypatch.setenv("FLASK_DEBUG", "true")
    assert _env_bool("FLASK_DEBUG", default=False) is True


def test_debug_and_sms_flags_are_booleans():
    # Never expose the literal string "false" as a truthy value.
    assert isinstance(Config.DEBUG, bool)
    assert isinstance(Config.SMS_MOCK_FAIL, bool)


# --- production validation ------------------------------------------------


def test_production_missing_secret_key_fails():
    with pytest.raises(RuntimeError) as exc:
        validate_production_config(_production_data(SECRET_KEY=""))
    assert "SECRET_KEY" in str(exc.value)


def test_production_missing_jwt_secret_key_fails():
    with pytest.raises(RuntimeError) as exc:
        validate_production_config(_production_data(JWT_SECRET_KEY=""))
    assert "JWT_SECRET_KEY" in str(exc.value)


def test_production_missing_database_url_fails():
    with pytest.raises(RuntimeError) as exc:
        validate_production_config(_production_data(DATABASE_URL=""))
    assert "DATABASE_URL" in str(exc.value)


def test_production_insecure_secret_fails():
    with pytest.raises(RuntimeError) as exc:
        validate_production_config(_production_data(SECRET_KEY="dev-only-change-me"))
    assert "SECRET_KEY" in str(exc.value)


def test_production_short_secret_fails():
    with pytest.raises(RuntimeError) as exc:
        validate_production_config(_production_data(SECRET_KEY="short"))
    assert "SECRET_KEY" in str(exc.value)


def test_production_with_required_config_succeeds():
    validate_production_config(_production_data())


def test_production_error_does_not_leak_secret_value():
    with pytest.raises(RuntimeError) as exc:
        validate_production_config(_production_data(SECRET_KEY="short-secret"))
    assert "short-secret" not in str(exc.value)


def test_create_app_production_fails_without_secrets():
    class IncompleteProductionConfig:
        APP_ENV = "production"
        SECRET_KEY = ""
        JWT_SECRET_KEY = ""
        DATABASE_URL = ""

    with pytest.raises(RuntimeError):
        create_app(IncompleteProductionConfig)


def test_create_app_production_succeeds_with_config():
    app = create_app(ProductionConfig)
    assert app.config["APP_ENV"] == "production"


# --- GONLINE compatibility ------------------------------------------------


def test_gonline_settings_are_exposed():
    assert hasattr(Config, "SMS_PROVIDER")
    assert hasattr(Config, "SMS_API_KEY")
    assert hasattr(Config, "SMS_SENDER_ID")
    assert hasattr(Config, "SMS_MOCK_FAIL")


# --- legacy sanity --------------------------------------------------------


def test_database_config_loads(app):
    assert app.config["SQLALCHEMY_DATABASE_URI"]
    assert app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] is False


def test_default_database_uri_is_configured():
    assert Config.SQLALCHEMY_DATABASE_URI
