from flask import Blueprint, jsonify, request

from app.services import shop_service
from app.utils.auth import get_current_user, has_shop_access, roles_required

shops_bp = Blueprint("shops", __name__)

SHOP_FIELDS = {"name", "location", "phone", "sender_id", "status"}


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


@shops_bp.get("/shops")
@roles_required("SUPER_ADMIN", "SHOP_MANAGER", "STAFF")
def list_shops():
    user = get_current_user()
    shops = shop_service.list_shops_for_actor(user)
    return jsonify({"shops": [s.to_dict() for s in shops]}), 200


@shops_bp.post("/shops")
@roles_required("SUPER_ADMIN")
def create_shop():
    data, err = _parse_body()
    if err:
        return err
    rejected = _reject_unknown(data, SHOP_FIELDS)
    if rejected:
        return rejected

    user = get_current_user()
    shop, error = shop_service.create_shop(user, data)
    if error:
        status, message = error
        return jsonify({"error": message}), status
    return jsonify({"shop": shop.to_dict()}), 201


@shops_bp.get("/shops/<shop_id>")
@roles_required("SUPER_ADMIN", "SHOP_MANAGER", "STAFF")
def get_shop(shop_id):
    user = get_current_user()
    shop = shop_service.get_shop(shop_id)
    if shop is None:
        return jsonify({"error": "Shop not found."}), 404
    if not has_shop_access(user, shop_id):
        return jsonify({"error": "You do not have access to this shop."}), 403
    return jsonify({"shop": shop.to_dict()}), 200


@shops_bp.patch("/shops/<shop_id>")
@roles_required("SUPER_ADMIN")
def update_shop(shop_id):
    data, err = _parse_body()
    if err:
        return err
    rejected = _reject_unknown(data, SHOP_FIELDS)
    if rejected:
        return rejected

    user = get_current_user()
    shop = shop_service.get_shop(shop_id)
    if shop is None:
        return jsonify({"error": "Shop not found."}), 404

    shop, error = shop_service.update_shop(user, shop, data)
    if error:
        status, message = error
        return jsonify({"error": message}), status
    return jsonify({"shop": shop.to_dict()}), 200
