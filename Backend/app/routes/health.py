from flask import Blueprint, current_app, jsonify
from sqlalchemy import text

from app.extensions import db

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "Great Alexender Enterprise API",
        }
    )


@health_bp.get("/health/db")
def db_health():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "ok", "database": "connected"})
    except Exception as exc:
        current_app.logger.error("Database health check failed: %s", exc)
        return jsonify({"status": "error", "database": "unavailable"}), 503
