from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required
from werkzeug.security import check_password_hash

from app.models.user import User, UserStatus
from app.utils.auth import get_current_user

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/auth/login")
def login():
    """
    POST /api/auth/login

    Body: {"email": "...", "password": "..."}

    Returns an access token and safe user info on success (200).
    400 for malformed input, 401 for invalid credentials, 403 for an
    inactive account.
    """
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"message": "Invalid request body."}), 400

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"message": "Email and password are required."}), 400

    user = User.query.filter_by(email=email).first()
    if user is None or not check_password_hash(user.password_hash, password):
        return jsonify({"message": "Invalid email or password."}), 401

    if user.status != UserStatus.ACTIVE:
        return jsonify({"message": "Account is inactive."}), 403

    access_token = create_access_token(
        identity=user.id,
        additional_claims={"role": user.role, "shop_id": user.shop_id},
    )

    return jsonify({"access_token": access_token, "user": user.to_dict()}), 200


@auth_bp.get("/auth/me")
@jwt_required()
def me():
    """
    GET /api/auth/me

    Requires: Authorization: Bearer <access_token>

    Returns the currently authenticated user's safe information.
    """
    user = get_current_user()
    if user is None:
        return jsonify({"message": "Account is inactive or no longer exists."}), 401

    return jsonify({"user": user.to_dict()}), 200
