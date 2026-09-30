from flask import Flask

from app.config import Config
from app.routes.health import health_bp


def create_app(config_object: type[Config] = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object)

    from app.extensions import cors

    cors.init_app(app, resources={r"/api/*": {"origins": config_object.CORS_ORIGINS}})

    app.register_blueprint(health_bp, url_prefix="/api")

    @app.route("/")
    def index():
        return {
            "service": "Great Alexender Enterprise API",
            "status": "ok",
        }

    return app
