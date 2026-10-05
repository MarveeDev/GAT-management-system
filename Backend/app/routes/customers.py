from flask import Blueprint, jsonify

from app.services import customer_service
from app.utils.auth import get_current_user, roles_required

customers_bp = Blueprint("customers", __name__)


@customers_bp.get("/customers")
@roles_required("SUPER_ADMIN", "SHOP_MANAGER", "STAFF")
def list_customers():
    actor = get_current_user()
    customers = customer_service.list_customers(actor)
    return jsonify({"customers": customers}), 200
