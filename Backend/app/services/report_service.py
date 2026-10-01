from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.purchase import Purchase
from app.models.shop import Shop
from app.models.sms_log import SMSLog, SMSStatus
from app.models.user import UserRole

# Africa/Accra is UTC+0 and does not observe daylight saving time, so the
# reporting timezone is identical to UTC. All report date boundaries are
# computed and compared as timezone-aware UTC datetimes.
REPORT_TIMEZONE = timezone.utc

PRESETS = (
    "today",
    "yesterday",
    "last_7_days",
    "last_30_days",
    "this_month",
    "previous_month",
    "custom",
)

DEFAULT_PRESET = "last_30_days"

_MONEY_QUANT = Decimal("0.01")


class ReportError(Exception):
    """Domain error carrying an HTTP status for report endpoints."""

    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def _now() -> datetime:
    return datetime.now(REPORT_TIMEZONE)


def _start_of_day(dt: datetime) -> datetime:
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def _shift_month(dt: datetime, delta: int) -> datetime:
    index = dt.month - 1 + delta
    year = dt.year + index // 12
    month = index % 12 + 1
    return dt.replace(year=year, month=month, day=1)


def _parse_boundary(value, *, is_end: bool = False):
    """Parse a report date boundary.

    A date-only value (``YYYY-MM-DD``) is interpreted as midnight in the
    reporting timezone. For an exclusive end bound, a date-only value is
    advanced to the start of the following day so the whole day is included.
    """
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None

    try:
        if len(text) == 10 and "T" not in text and " " not in text:
            day = date.fromisoformat(text)
            dt = datetime.combine(day, time.min, tzinfo=REPORT_TIMEZONE)
            if is_end:
                dt += timedelta(days=1)
            return dt
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        raise ReportError(f"Invalid date: {value}", 400)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=REPORT_TIMEZONE)
    else:
        dt = dt.astimezone(REPORT_TIMEZONE)
    return dt


def _preset_range(preset: str) -> tuple[datetime, datetime]:
    now = _now()
    today_start = _start_of_day(now)
    day = timedelta(days=1)

    if preset == "today":
        return today_start, today_start + day
    if preset == "yesterday":
        return today_start - day, today_start
    if preset == "last_7_days":
        return today_start - timedelta(days=6), today_start + day
    if preset == "last_30_days":
        return today_start - timedelta(days=29), today_start + day
    if preset == "this_month":
        first = today_start.replace(day=1)
        return first, _shift_month(first, 1)
    if preset == "previous_month":
        first_this = today_start.replace(day=1)
        return _shift_month(first_this, -1), first_this

    raise ReportError(f"Invalid preset: {preset}", 400)


def resolve_report_date_range(
    preset: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> tuple[datetime | None, datetime | None]:
    """Resolve report date bounds as a half-open interval ``[start, end)``.

    Both bounds are timezone-aware UTC datetimes (or ``None`` for an unbounded
    side). Raises :class:`ReportError` (400) for invalid input.
    """
    if preset and preset not in PRESETS:
        raise ReportError(f"Invalid preset: {preset}", 400)

    if not preset and not date_from and not date_to:
        preset = DEFAULT_PRESET

    if preset and preset != "custom":
        if date_from or date_to:
            raise ReportError(
                "preset cannot be combined with date_from/date_to.", 400
            )
        start, end = _preset_range(preset)
    else:
        start = _parse_boundary(date_from, is_end=False)
        end = _parse_boundary(date_to, is_end=True)

    if start is not None and end is not None and start > end:
        raise ReportError("date_from must not be after date_to.", 400)

    return start, end


def resolve_report_shop_ids(actor, requested_shop_id: str | None):
    """Return the list of shop ids to include, or ``None`` meaning "all shops".

    SUPER_ADMIN may report on all shops or filter to one shop. SHOP_MANAGER and
    STAFF are always restricted to their own assigned shop. Raises
    :class:`ReportError` (403/404) when access is invalid or denied.
    """
    if actor.role == UserRole.SUPER_ADMIN:
        if not requested_shop_id:
            return None
        shop = _lookup_shop(requested_shop_id)
        if shop is None:
            raise ReportError("Shop not found.", 404)
        return [shop.id]

    if not actor.shop_id:
        raise ReportError("You do not have access to any shop.", 403)
    if requested_shop_id and requested_shop_id != actor.shop_id:
        raise ReportError("You do not have access to this shop.", 403)
    return [actor.shop_id]


def _lookup_shop(shop_id: str):
    try:
        UUID(shop_id)
    except (ValueError, AttributeError):
        return None
    return db.session.get(Shop, shop_id)


def _scoped_purchase_query(shop_ids, start, end):
    query = Purchase.query
    if shop_ids is not None:
        query = query.filter(Purchase.shop_id.in_(shop_ids))
    if start is not None:
        query = query.filter(Purchase.created_at >= start)
    if end is not None:
        query = query.filter(Purchase.created_at < end)
    return query


def _scoped_sms_query(shop_ids, start, end):
    query = SMSLog.query
    if shop_ids is not None:
        query = query.filter(SMSLog.shop_id.in_(shop_ids))
    if start is not None:
        query = query.filter(SMSLog.created_at >= start)
    if end is not None:
        query = query.filter(SMSLog.created_at < end)
    return query


def _money(value) -> Decimal:
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def _money_str(value: Decimal) -> str:
    return format(value.quantize(_MONEY_QUANT, rounding=ROUND_HALF_UP), "f")


def _range_dict(start, end) -> dict:
    return {
        "start": start.isoformat() if start is not None else None,
        "end": end.isoformat() if end is not None else None,
    }


def get_summary(shop_ids, start, end) -> dict:
    """Aggregate the overview metrics for the given scope and date range.

    All metrics are computed in the database with SQL aggregates; no purchase
    rows are loaded into Python.
    """
    purchases = _scoped_purchase_query(shop_ids, start, end)
    total_purchases = purchases.count()

    total_sales = _money(
        purchases.with_entities(func.sum(Purchase.amount)).scalar()
    )
    unique_customers = purchases.with_entities(
        func.count(func.distinct(Purchase.customer_id))
    ).scalar()

    sms = _scoped_sms_query(shop_ids, start, end)
    sms_sent = sms.filter(SMSLog.status == SMSStatus.SENT).count()
    sms_failed = sms.filter(SMSLog.status == SMSStatus.FAILED).count()
    sms_pending = sms.filter(SMSLog.status == SMSStatus.PENDING).count()

    average_purchase_value = None
    if total_purchases:
        average_purchase_value = (total_sales / total_purchases).quantize(
            _MONEY_QUANT, rounding=ROUND_HALF_UP
        )

    return {
        "range": _range_dict(start, end),
        "total_purchases": total_purchases,
        "total_sales": _money_str(total_sales),
        "average_purchase_value": (
            _money_str(average_purchase_value)
            if average_purchase_value is not None
            else None
        ),
        "unique_customers": unique_customers,
        "sms_sent": sms_sent,
        "sms_failed": sms_failed,
        "sms_pending": sms_pending,
    }


def _sales_row(purchase) -> dict:
    customer = purchase.customer
    shop = purchase.shop
    staff = purchase.staff
    return {
        "id": purchase.id,
        "date": purchase.created_at.isoformat() if purchase.created_at else None,
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
        }
        if customer
        else None,
        "product": purchase.product,
        "amount": _money_str(_money(purchase.amount)),
        "currency": purchase.currency,
        "shop": {"id": shop.id, "name": shop.name} if shop else None,
        "recorded_by": {
            "id": staff.id,
            "name": staff.name,
            "email": staff.email,
            "role": staff.role,
        }
        if staff
        else None,
    }


def get_sales(shop_ids, start, end, page: int = 1, per_page: int = 25) -> dict:
    """Return the paginated sales report for the given scope and date range.

    The summary reflects the entire scope (not just the current page). All
    aggregation is performed in the database; only the current page of rows is
    loaded into Python.
    """
    base = _scoped_purchase_query(shop_ids, start, end)
    total = base.count()

    total_sales = _money(base.with_entities(func.sum(Purchase.amount)).scalar())
    average = None
    if total:
        average = (total_sales / total).quantize(
            _MONEY_QUANT, rounding=ROUND_HALF_UP
        )

    pages = (total + per_page - 1) // per_page

    purchases = (
        base.options(
            joinedload(Purchase.customer),
            joinedload(Purchase.staff),
            joinedload(Purchase.shop),
        )
        .order_by(Purchase.created_at.desc(), Purchase.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "sales": [_sales_row(p) for p in purchases],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": pages,
        },
        "summary": {
            "total_purchases": total,
            "total_sales": _money_str(total_sales),
            "average_purchase_value": (
                _money_str(average) if average is not None else None
            ),
        },
        "range": _range_dict(start, end),
    }


def _success_rate_str(sent: int, total: int) -> str:
    """Return the provider-accepted success rate as a 2-decimal string.

    ``0.00`` is returned when there are no SMS records (avoids divide-by-zero).
    """
    if not total:
        return "0.00"
    rate = (Decimal(sent) / Decimal(total) * Decimal(100)).quantize(
        _MONEY_QUANT, rounding=ROUND_HALF_UP
    )
    return format(rate, "f")


def _sms_row(sms_log) -> dict:
    customer = sms_log.customer
    shop = sms_log.shop
    return {
        "id": sms_log.id,
        "date": sms_log.created_at.isoformat() if sms_log.created_at else None,
        "phone_number": sms_log.phone_number,
        "status": sms_log.status,
        "provider": sms_log.provider,
        "shop": {"id": shop.id, "name": shop.name} if shop else None,
        "customer": {
            "id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
        }
        if customer
        else None,
        "purchase_id": sms_log.purchase_id,
        "error_message": sms_log.error_message,
    }


def get_sms_report(shop_ids, start, end, page: int = 1, per_page: int = 25) -> dict:
    """Return the paginated SMS report for the given scope and date range.

    The summary covers the entire scope (not just the current page) and is
    computed with SQL aggregates. Only the current page of rows is loaded.
    """
    base = _scoped_sms_query(shop_ids, start, end)
    total_sms = base.count()
    sms_sent = base.filter(SMSLog.status == SMSStatus.SENT).count()
    sms_failed = base.filter(SMSLog.status == SMSStatus.FAILED).count()
    sms_pending = base.filter(SMSLog.status == SMSStatus.PENDING).count()

    pages = (total_sms + per_page - 1) // per_page

    logs = (
        base.options(joinedload(SMSLog.customer), joinedload(SMSLog.shop))
        .order_by(SMSLog.created_at.desc(), SMSLog.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return {
        "summary": {
            "total_sms": total_sms,
            "sms_sent": sms_sent,
            "sms_failed": sms_failed,
            "sms_pending": sms_pending,
            "success_rate": _success_rate_str(sms_sent, total_sms),
        },
        "sms": [_sms_row(log) for log in logs],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total_sms,
            "pages": pages,
        },
        "range": _range_dict(start, end),
    }
