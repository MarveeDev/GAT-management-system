from flask import Flask

from app.config import Config
from app.extensions import cors, db, migrate


def create_app(config_object: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    from app.routes.health import health_bp

    app.register_blueprint(health_bp, url_prefix="/api")

    from app import models  # noqa: F401  (register models with SQLAlchemy)

    register_commands(app)

    @app.route("/")
    def index():
        return {
            "service": "Great Alexender Enterprise API",
            "status": "ok",
        }

    return app


def register_commands(app: Flask) -> None:
    from app import commands

    commands.init_cli(app)
