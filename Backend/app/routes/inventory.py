from flask import Blueprint, jsonify, request

from app.services import inventory_service
from app.utils.auth import get_current_user, roles_required

inventory_bp = Blueprint("inventory", __name__)

INVENTORY_FIELDS = {"product_id", "shop_id", "quantity"}


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


@inventory_bp.get("/inventory")
@roles_required("SUPER_ADMIN", "SHOP_MANAGER", "STAFF")
def list_inventory():
    actor = get_current_user()
    inventories, error = inventory_service.list_inventory(
        actor,
        shop_id=request.args.get("shop_id"),
        product_id=request.args.get("product_id"),
    )
    if error:
        status, message = error
        return jsonify({"error": message}), status
    return jsonify({"inventory": [i.to_dict() for i in inventories]}), 200


@inventory_bp.post("/inventory")
@roles_required("SUPER_ADMIN")
def set_stock():
    data, err = _parse_body()
    if err:
        return err
    rejected = _reject_unknown(data, INVENTORY_FIELDS)
    if rejected:
        return rejected

    actor = get_current_user()
    if not data.get("product_id") or not data.get("shop_id"):
        return jsonify({"error": "product_id and shop_id are required."}), 400

    inventory, error = inventory_service.set_stock(
        actor,
        product_id=data["product_id"],
        shop_id=data["shop_id"],
        quantity=data.get("quantity"),
    )
    if error:
        status, message = error
        return jsonify({"error": message}), status
    return jsonify({"inventory": inventory.to_dict()}), 200


@inventory_bp.get("/inventory/<product_id>")
@roles_required("SUPER_ADMIN", "SHOP_MANAGER", "STAFF")
def get_product_inventory(product_id):
    actor = get_current_user()
    inventories, error = inventory_service.get_product_inventory(actor, product_id)
    if error:
        status, message = error
        return jsonify({"error": message}), status
    return jsonify({"inventory": [i.to_dict() for i in inventories]}), 200


@inventory_bp.get("/inventory/<product_id>/movements")
@roles_required("SUPER_ADMIN")
def list_movements(product_id):
    actor = get_current_user()
    movements, error = inventory_service.list_movements(
        actor, product_id, shop_id=request.args.get("shop_id")
    )
    if error:
        status, message = error
        return jsonify({"error": message}), status
    return jsonify({"movements": [m.to_dict() for m in movements]}), 200
