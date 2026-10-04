from flask import Blueprint, jsonify, request

from app.services import product_service
from app.utils.auth import get_current_user, roles_required

products_bp = Blueprint("products", __name__)

PRODUCT_FIELDS = {"name", "category", "minimum_price", "maximum_price", "status"}


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


@products_bp.get("/products")
@roles_required("SUPER_ADMIN", "SHOP_MANAGER", "STAFF")
def list_products():
    actor = get_current_user()
    products = product_service.list_products(
        actor,
        search=request.args.get("search"),
        status=request.args.get("status"),
    )
    return jsonify({"products": [p.to_dict() for p in products]}), 200


@products_bp.post("/products")
@roles_required("SUPER_ADMIN")
def create_product():
    data, err = _parse_body()
    if err:
        return err
    rejected = _reject_unknown(data, PRODUCT_FIELDS)
    if rejected:
        return rejected

    actor = get_current_user()
    product, error = product_service.create_product(actor, data)
    if error:
        status, message = error
        return jsonify({"error": message}), status
    return jsonify({"product": product.to_dict()}), 201


@products_bp.get("/products/<product_id>")
@roles_required("SUPER_ADMIN", "SHOP_MANAGER", "STAFF")
def get_product(product_id):
    actor = get_current_user()
    product, error = product_service.get_visible_product(actor, product_id)
    if error:
        status, message = error
        return jsonify({"error": message}), status
    return jsonify({"product": product.to_dict()}), 200


@products_bp.patch("/products/<product_id>")
@roles_required("SUPER_ADMIN")
def update_product(product_id):
    data, err = _parse_body()
    if err:
        return err
    rejected = _reject_unknown(data, PRODUCT_FIELDS)
    if rejected:
        return rejected

    actor = get_current_user()
    product = product_service.get_product(product_id)
    if product is None:
        return jsonify({"error": "Product not found."}), 404

    product, error = product_service.update_product(actor, product, data)
    if error:
        status, message = error
        return jsonify({"error": message}), status
    return jsonify({"product": product.to_dict()}), 200
