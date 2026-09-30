from app.config import Config


def test_database_config_loads(app):
    assert app.config["SQLALCHEMY_DATABASE_URI"]
    assert app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] is False


def test_default_database_uri_is_configured():
    assert Config.SQLALCHEMY_DATABASE_URI
