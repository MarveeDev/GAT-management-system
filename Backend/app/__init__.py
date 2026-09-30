from flask import Flask

from app.config import Config
from app.extensions import cors, db, jwt, migrate


def create_app(config_object: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    from app.routes.auth import auth_bp
    from app.routes.health import health_bp
    from app.routes.shops import shops_bp
    from app.routes.users import users_bp

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(shops_bp, url_prefix="/api")
    app.register_blueprint(users_bp, url_prefix="/api")

    from app import models  # noqa: F401  (register models with SQLAlchemy)

    from app.utils.auth import register_jwt_error_handlers

    register_jwt_error_handlers(jwt)

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
