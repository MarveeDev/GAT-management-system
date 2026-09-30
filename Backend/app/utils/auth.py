from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.extensions import db
from app.models.user import User, UserRole, UserStatus


def get_current_user() -> User | None:
    """Load the authenticated user from the JWT identity and the database.

    Returns None if there is no identity, the user no longer exists, or the
    user has been deactivated. Authorization must always be based on the
    current database record, never on client-provided claims.
    """
    identity = get_jwt_identity()
    if identity is None:
        return None

    user = db.session.get(User, identity)
    if user is None or user.status != UserStatus.ACTIVE:
        return None

    return user


def roles_required(*roles: str):
    """Protect a route and require the current user to have one of *roles*.

    Verifies a JWT is present, loads the user from the database, and rejects
    inactive users (401) and users without a permitted role (403).
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = get_current_user()
            if user is None:
                return jsonify(
                    {"message": "Account is inactive or no longer exists."}
                ), 401
            if user.role not in roles:
                return jsonify(
                    {"message": "You do not have permission to perform this action."}
                ), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def has_shop_access(user: User, requested_shop_id: str | None) -> bool:
    """Return True if the user may access the requested shop.

    SUPER_ADMIN may access any shop. SHOP_MANAGER and STAFF may only access
    their own assigned shop. This is the backend source of truth for
    shop-level authorization.
    """
    if user.role == UserRole.SUPER_ADMIN:
        return True
    return requested_shop_id is not None and requested_shop_id == user.shop_id


def shop_access_denied_response():
    return jsonify({"message": "You do not have access to this shop."}), 403


def register_jwt_error_handlers(jwt) -> None:
    @jwt.unauthorized_loader
    def unauthorized(_reason):
        return jsonify(
            {"message": "Missing or invalid authorization header."}
        ), 401

    @jwt.invalid_token_loader
    def invalid_token(_reason):
        return jsonify({"message": "Invalid token."}), 401

    @jwt.expired_token_loader
    def expired_token(_jwt_header, _jwt_payload):
        return jsonify({"message": "Token has expired."}), 401
