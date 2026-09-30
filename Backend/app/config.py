import os
from datetime import timedelta

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-jwt-secret-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.getenv("JWT_ACCESS_TOKEN_HOURS", "12"))
    )

    CORS_ORIGINS = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if origin.strip()
    ]

    DEBUG = os.getenv("FLASK_DEBUG", "1") == "1"

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'dev.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # SMS provider (mock by default; never sends real SMS)
    SMS_PROVIDER = os.getenv("SMS_PROVIDER", "mock")
    SMS_API_KEY = os.getenv("SMS_API_KEY", "")
    SMS_API_SECRET = os.getenv("SMS_API_SECRET", "")
    SMS_SENDER_ID = os.getenv("SMS_SENDER_ID", "")
    SMS_MOCK_FAIL = os.getenv("SMS_MOCK_FAIL", "0") == "1"
