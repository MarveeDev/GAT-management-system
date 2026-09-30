import pytest
from sqlalchemy.pool import StaticPool

from app import create_app
from app.extensions import db as _db


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret"
    JWT_SECRET_KEY = "test-jwt-secret-key-that-is-at-least-32-bytes-long"
    DEBUG = False
    CORS_ORIGINS = ["http://localhost:5173"]
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "poolclass": StaticPool,
        "connect_args": {"check_same_thread": False},
    }


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        _db.create_all()
    yield app
    with app.app_context():
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def session(app):
    with app.app_context():
        yield _db.session
