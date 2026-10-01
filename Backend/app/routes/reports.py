from flask import Blueprint, jsonify, request

from app.services import report_service
from app.utils.auth import get_current_user, roles_required

reports_bp = Blueprint("reports", __name__)


def _parse_int(value, default, param, min_value=None, max_value=None):
    if value is None:
        return default
    try:
        parsed = int(str(value))
    except (ValueError, TypeError):
        raise report_service.ReportError(f"Invalid {param}.", 400)
    if min_value is not None and parsed < min_value:
        raise report_service.ReportError(
            f"{param} must be at least {min_value}.", 400
        )
    if max_value is not None and parsed > max_value:
        raise report_service.ReportError(
            f"{param} must be at most {max_value}.", 400
        )
    return parsed


@reports_bp.get("/reports/summary")
@roles_required("SUPER_ADMIN", "SHOP_MANAGER", "STAFF")
def summary():
    actor = get_current_user()

    try:
        start, end = report_service.resolve_report_date_range(
            preset=request.args.get("preset"),
            date_from=request.args.get("date_from"),
            date_to=request.args.get("date_to"),
        )
        shop_ids = report_service.resolve_report_shop_ids(
            actor, request.args.get("shop_id")
        )
    except report_service.ReportError as exc:
        return jsonify({"error": str(exc)}), exc.status

    summary_data = report_service.get_summary(shop_ids, start, end)
    return jsonify({"summary": summary_data}), 200


@reports_bp.get("/reports/sales")
@roles_required("SUPER_ADMIN", "SHOP_MANAGER", "STAFF")
def sales():
    actor = get_current_user()

    try:
        start, end = report_service.resolve_report_date_range(
            preset=request.args.get("preset"),
            date_from=request.args.get("date_from"),
            date_to=request.args.get("date_to"),
        )
        shop_ids = report_service.resolve_report_shop_ids(
            actor, request.args.get("shop_id")
        )
        page = _parse_int(request.args.get("page"), 1, "page", min_value=1)
        per_page = _parse_int(
            request.args.get("per_page"), 25, "per_page", min_value=1, max_value=100
        )
    except report_service.ReportError as exc:
        return jsonify({"error": str(exc)}), exc.status

    result = report_service.get_sales(shop_ids, start, end, page, per_page)
    return jsonify(result), 200


@reports_bp.get("/reports/sms")
@roles_required("SUPER_ADMIN", "SHOP_MANAGER", "STAFF")
def sms():
    actor = get_current_user()

    try:
        start, end = report_service.resolve_report_date_range(
            preset=request.args.get("preset"),
            date_from=request.args.get("date_from"),
            date_to=request.args.get("date_to"),
        )
        shop_ids = report_service.resolve_report_shop_ids(
            actor, request.args.get("shop_id")
        )
        page = _parse_int(request.args.get("page"), 1, "page", min_value=1)
        per_page = _parse_int(
            request.args.get("per_page"), 25, "per_page", min_value=1, max_value=100
        )
    except report_service.ReportError as exc:
        return jsonify({"error": str(exc)}), exc.status

    result = report_service.get_sms_report(shop_ids, start, end, page, per_page)
    return jsonify(result), 200


@reports_bp.get("/reports/shops")
@roles_required("SUPER_ADMIN", "SHOP_MANAGER", "STAFF")
def shops():
    actor = get_current_user()

    try:
        start, end = report_service.resolve_report_date_range(
            preset=request.args.get("preset"),
            date_from=request.args.get("date_from"),
            date_to=request.args.get("date_to"),
        )
        shop_ids = report_service.resolve_report_shop_ids(
            actor, request.args.get("shop_id")
        )
    except report_service.ReportError as exc:
        return jsonify({"error": str(exc)}), exc.status

    result = report_service.get_shop_performance(shop_ids, start, end)
    return jsonify(result), 200


@reports_bp.get("/reports/staff")
@roles_required("SUPER_ADMIN", "SHOP_MANAGER", "STAFF")
def staff():
    actor = get_current_user()

    try:
        start, end = report_service.resolve_report_date_range(
            preset=request.args.get("preset"),
            date_from=request.args.get("date_from"),
            date_to=request.args.get("date_to"),
        )
        shop_ids = report_service.resolve_report_shop_ids(
            actor, request.args.get("shop_id")
        )
    except report_service.ReportError as exc:
        return jsonify({"error": str(exc)}), exc.status

    result = report_service.get_staff_activity(shop_ids, start, end)
    return jsonify(result), 200
