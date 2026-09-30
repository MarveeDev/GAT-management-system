from flask import Blueprint, jsonify, request

from app.services import user_service
from app.utils.auth import get_current_user, roles_required

users_bp = Blueprint("users", __name__)

USER_CREATE_FIELDS = {"name", "email", "phone", "password", "role", "shop_id"}
USER_UPDATE_FIELDS = {"name", "phone", "role", "shop_id", "status"}
PASSWORD_FIELDS = {"password"}


def _parse_body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None, (jsonify({"error": "Invalid request body."}), 400)
    return data, None


def _reject_unknown(data, allowed):
    unknown = set(data) - allowed
    if unknown:
        return jsonify(
            {"error": f"Unknown field(s): {', '.join(sorted(unknown))}"}
        ), 400
    return None


@users_bp.get("/users")
@roles_required("SUPER_ADMIN", "SHOP_MANAGER")
def list_users():
    user = get_current_user()
    users = user_service.list_users(
        user,
        shop_id=request.args.get("shop_id"),
        role=request.args.get("role"),
        status=request.args.get("status"),
    )
    return jsonify({"users": [u.to_dict() for u in users]}), 200


@users_bp.post("/users")
@roles_required("SUPER_ADMIN", "SHOP_MANAGER")
def create_user():
    data, err = _parse_body()
    if err:
        return err
    rejected = _reject_unknown(data, USER_CREATE_FIELDS)
    if rejected:
        return rejected

    actor = get_current_user()
    user, error = user_service.create_user(actor, data)
    if error:
        status, message = error
        return jsonify({"error": message}), status
    return jsonify({"user": user.to_dict()}), 201


@users_bp.get("/users/<user_id>")
@roles_required("SUPER_ADMIN", "SHOP_MANAGER", "STAFF")
def get_user(user_id):
    actor = get_current_user()
    user, error = user_service.get_visible_user(actor, user_id)
    if error:
        status, message = error
        return jsonify({"error": message}), status
    return jsonify({"user": user.to_dict()}), 200


@users_bp.patch("/users/<user_id>")
@roles_required("SUPER_ADMIN", "SHOP_MANAGER")
def update_user(user_id):
    data, err = _parse_body()
    if err:
        return err
    rejected = _reject_unknown(data, USER_UPDATE_FIELDS)
    if rejected:
        return rejected

    actor = get_current_user()
    target = user_service.get_user(user_id)
    if target is None:
        return jsonify({"error": "User not found."}), 404

    user, error = user_service.update_user(actor, target, data)
    if error:
        status, message = error
        return jsonify({"error": message}), status
    return jsonify({"user": user.to_dict()}), 200


@users_bp.patch("/users/<user_id>/password")
@roles_required("SUPER_ADMIN", "SHOP_MANAGER")
def update_user_password(user_id):
    data, err = _parse_body()
    if err:
        return err
    rejected = _reject_unknown(data, PASSWORD_FIELDS)
    if rejected:
        return rejected

    actor = get_current_user()
    target = user_service.get_user(user_id)
    if target is None:
        return jsonify({"error": "User not found."}), 404

    user, error = user_service.update_password(actor, target, data.get("password") or "")
    if error:
        status, message = error
        return jsonify({"error": message}), status
    return jsonify({"user": user.to_dict()}), 200
