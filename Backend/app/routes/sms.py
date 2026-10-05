from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

from app.services import sms_service
from app.utils.auth import get_current_user, roles_required

sms_bp = Blueprint("sms", __name__)


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


def _parse_ids(value):
    if not value:
        return None
    ids = [item.strip() for item in value.split(",") if item.strip()]
    return ids or None


@sms_bp.get("/sms")
@roles_required("SUPER_ADMIN", "SHOP_MANAGER", "STAFF")
def list_sms_logs():
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

    logs, pagination = sms_service.list_sms_logs(
        actor,
        shop_id=request.args.get("shop_id"),
        purchase_id=request.args.get("purchase_id"),
        purchase_ids=_parse_ids(request.args.get("purchase_ids")),
        customer_id=request.args.get("customer_id"),
        status=request.args.get("status"),
        date_from=date_from,
        date_to=date_to,
        page=page,
        per_page=per_page,
    )
    return jsonify(
        {"sms_logs": [log.to_dict() for log in logs], "pagination": pagination}
    ), 200


@sms_bp.get("/sms/<sms_id>")
@roles_required("SUPER_ADMIN", "SHOP_MANAGER", "STAFF")
def get_sms_log(sms_id):
    actor = get_current_user()
    sms_log, error = sms_service.get_sms_log(actor, sms_id)
    if error:
        status, message = error
        return jsonify({"error": message}), status
    return jsonify({"sms": sms_log.to_dict()}), 200


@sms_bp.post("/sms/<sms_id>/retry")
@roles_required("SUPER_ADMIN", "SHOP_MANAGER", "STAFF")
def retry_sms(sms_id):
    actor = get_current_user()
    sms_log, error = sms_service.get_sms_log(actor, sms_id)
    if error:
        status, message = error
        return jsonify({"error": message}), status

    updated, error = sms_service.retry_sms(actor, sms_log)
    if error:
        status, message = error
        return jsonify({"error": message}), status
    return jsonify({"sms": updated.to_dict()}), 200
