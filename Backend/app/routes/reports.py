from flask import Blueprint, jsonify, request

from app.services import report_service
from app.utils.auth import get_current_user, roles_required

reports_bp = Blueprint("reports", __name__)


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
