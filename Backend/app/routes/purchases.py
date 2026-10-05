from datetime import datetime, timedelta

from flask import Blueprint, current_app, jsonify, request

from app.services import purchase_service, sms_service
from app.utils.auth import get_current_user, roles_required

purchases_bp = Blueprint("purchases", __name__)

PURCHASE_FIELDS = {"shop_id", "customer_id", "customer", "product", "product_id", "quantity", "unit_price", "amount", "currency"}


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


def _parse_int(value, default, param, min_value=None, max_value=None):
    if value is None:
        value = default
    try:
        parsed = int(value)
    except (ValueError, TypeError):
        return None, (jsonify({"error": f"Invalid {param}."}), 400)
    if min_value is not None and parsed < min_value:
        parsed = min_value
    if max_value is not None and parsed > max_value:
        parsed = max_value
    return parsed, None


def _parse_date(value, end_of_day=False):
    if not value:
        return None
    text = value.strip()
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError(f"Invalid date: {value}")
    if end_of_day and len(text) == 10 and "T" not in text:
        dt = dt + timedelta(days=1) - timedelta(microseconds=1)
    return dt


@purchases_bp.post("/purchases")
@roles_required("SUPER_ADMIN", "SHOP_MANAGER", "STAFF")
def create_purchase():
    data, err = _parse_body()
    if err:
        return err
    rejected = _reject_unknown(data, PURCHASE_FIELDS)
    if rejected:
        return rejected

    actor = get_current_user()
    purchase, error = purchase_service.create_purchase(actor, data)
    if error:
        status, message = error
        return jsonify({"error": message}), status

    try:
        _, sms_info = sms_service.send_purchase_sms(purchase)
    except Exception as exc:
        current_app.logger.error("SMS workflow error: %s", exc)
        sms_info = {"status": "FAILED", "error": "SMS delivery failed."}

    return jsonify({"purchase": purchase.to_dict(), "sms": sms_info}), 201


@purchases_bp.get("/purchases")
@roles_required("SUPER_ADMIN", "SHOP_MANAGER", "STAFF")
def list_purchases():
    actor = get_current_user()

    page, err = _parse_int(request.args.get("page"), 1, "page", min_value=1)
    if err:
        return err
    per_page, err = _parse_int(
        request.args.get("per_page"), 20, "per_page", min_value=1, max_value=100
    )
    if err:
        return err

    try:
        date_from = _parse_date(request.args.get("date_from"))
        date_to = _parse_date(request.args.get("date_to"), end_of_day=True)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    purchases, pagination, summary = purchase_service.list_purchases(
        actor,
        shop_id=request.args.get("shop_id"),
        staff_id=request.args.get("staff_id"),
        customer_id=request.args.get("customer_id"),
        date_from=date_from,
        date_to=date_to,
        search=request.args.get("search"),
        page=page,
        per_page=per_page,
    )
    return jsonify(
        {
            "purchases": [p.to_dict() for p in purchases],
            "pagination": pagination,
            "summary": summary,
        }
    ), 200


@purchases_bp.get("/purchases/<purchase_id>")
@roles_required("SUPER_ADMIN", "SHOP_MANAGER", "STAFF")
def get_purchase(purchase_id):
    actor = get_current_user()
    purchase, error = purchase_service.get_purchase(actor, purchase_id)
    if error:
        status, message = error
        return jsonify({"error": message}), status
    return jsonify({"purchase": purchase.to_dict()}), 200
