from flask import Flask, current_app, jsonify
from werkzeug.exceptions import HTTPException

from app.config import Config, validate_production_config
from app.extensions import cors, db, jwt, migrate


def create_app(config_object: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)

    if app.config.get("APP_ENV") == "production":
        validate_production_config(app.config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    from app.routes.auth import auth_bp
    from app.routes.health import health_bp
    from app.routes.inventory import inventory_bp
    from app.routes.products import products_bp
    from app.routes.purchases import purchases_bp
    from app.routes.reports import reports_bp
    from app.routes.shops import shops_bp
    from app.routes.sms import sms_bp
    from app.routes.users import users_bp

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(shops_bp, url_prefix="/api")
    app.register_blueprint(users_bp, url_prefix="/api")
    app.register_blueprint(purchases_bp, url_prefix="/api")
    app.register_blueprint(sms_bp, url_prefix="/api")
    app.register_blueprint(reports_bp, url_prefix="/api")
    app.register_blueprint(products_bp, url_prefix="/api")
    app.register_blueprint(inventory_bp, url_prefix="/api")

    from app import models  # noqa: F401  (register models with SQLAlchemy)

    from app.utils.auth import register_jwt_error_handlers

    register_jwt_error_handlers(jwt)

    @app.errorhandler(Exception)
    def handle_unhandled_error(error):
        if isinstance(error, HTTPException):
            return error
        current_app.logger.exception("Unhandled error: %s", error)
        return jsonify({"error": "An unexpected error occurred."}), 500

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
