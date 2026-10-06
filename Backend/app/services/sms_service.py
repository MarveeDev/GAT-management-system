from datetime import datetime, timezone

from flask import current_app

from app.extensions import db
from app.models.purchase import Purchase
from app.models.sms_log import SMSLog, SMSStatus
from app.models.user import User, UserRole
from app.services.audit_service import AuditAction, add_audit_log
from app.services.sms.base import ProviderResult
from app.services.sms.provider import get_sms_provider
from app.services.template_service import get_active_purchase_template, render_template


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _provider_name() -> str:
    return (current_app.config.get("SMS_PROVIDER") or "mock").strip().lower()


def _sender_id() -> str | None:
    return current_app.config.get("SMS_SENDER_ID") or None


def _mask_phone(phone: str | None) -> str:
    if not phone:
        return "N/A"
    return phone[-4:]


def build_sms_context(purchase: Purchase) -> dict:
    customer = purchase.customer
    shop = purchase.shop
    return {
        "customer_name": customer.name or "",
        "shop_name": shop.name or "",
        "product": purchase.product or "",
        "amount": str(purchase.amount) if purchase.amount is not None else "",
    }


def _call_provider(phone: str, message: str) -> ProviderResult:
    try:
        provider = get_sms_provider()
        return provider.send_sms(phone, message, sender_id=_sender_id())
    except Exception as exc:
        current_app.logger.error("SMS provider error: %s", exc)
        return ProviderResult(success=False, error_message="SMS delivery failed.")


def _apply_result(sms_log: SMSLog, result: ProviderResult, user_id: str, *, retry: bool = False) -> dict:
    if result.success:
        sms_log.status = SMSStatus.SENT
        sms_log.provider_message_id = result.provider_message_id
        sms_log.error_message = None
        sms_log.sent_at = utcnow()
        action = AuditAction.SMS_RETRY if retry else AuditAction.SMS_SENT
        add_audit_log(
            user_id,
            sms_log.shop_id,
            action,
            "SMS",
            sms_log.id,
            f"SMS {'retry' if retry else 'delivery'} succeeded for ...{_mask_phone(sms_log.phone_number)}.",
        )
        db.session.commit()
        return {"status": SMSStatus.SENT, "provider_message_id": result.provider_message_id}

    sms_log.status = SMSStatus.FAILED
    sms_log.error_message = result.error_message or "SMS delivery failed."
    action = AuditAction.SMS_RETRY if retry else AuditAction.SMS_FAILED
    add_audit_log(
        user_id,
        sms_log.shop_id,
        action,
        "SMS",
        sms_log.id,
        f"SMS {'retry' if retry else 'delivery'} failed for ...{_mask_phone(sms_log.phone_number)}.",
    )
    db.session.commit()
    return {"status": SMSStatus.FAILED, "error": sms_log.error_message}


def send_purchase_sms(purchase: Purchase) -> tuple[SMSLog, dict]:
    """Create an SMSLog for the purchase and attempt delivery.

    The purchase is already committed by the caller. SMS failures never affect
    the purchase.
    """
    provider_name = _provider_name()
    phone = purchase.customer.phone or ""

    template = get_active_purchase_template()
    if template is None:
        sms_log = SMSLog(
            shop_id=purchase.shop_id,
            purchase_id=purchase.id,
            customer_id=purchase.customer_id,
            phone_number=phone,
            message="",
            provider=provider_name,
            status=SMSStatus.FAILED,
            error_message="No active purchase SMS template configured.",
        )
        db.session.add(sms_log)
        db.session.flush()
        add_audit_log(
            purchase.staff_id,
            purchase.shop_id,
            AuditAction.SMS_FAILED,
            "SMS",
            sms_log.id,
            "SMS failed: no active purchase template configured.",
        )
        db.session.commit()
        return sms_log, {"status": SMSStatus.FAILED, "error": "No active purchase SMS template configured."}

    if not phone:
        sms_log = SMSLog(
            shop_id=purchase.shop_id,
            purchase_id=purchase.id,
            customer_id=purchase.customer_id,
            phone_number="",
            message=render_template(template.message, build_sms_context(purchase)),
            provider=provider_name,
            status=SMSStatus.FAILED,
            error_message="Customer has no phone number.",
        )
        db.session.add(sms_log)
        db.session.flush()
        add_audit_log(
            purchase.staff_id,
            purchase.shop_id,
            AuditAction.SMS_FAILED,
            "SMS",
            sms_log.id,
            "SMS failed: customer has no phone number.",
        )
        db.session.commit()
        return sms_log, {"status": SMSStatus.FAILED, "error": "Customer has no phone number."}

    message = render_template(template.message, build_sms_context(purchase))

    sms_log = SMSLog(
        shop_id=purchase.shop_id,
        purchase_id=purchase.id,
        customer_id=purchase.customer_id,
        phone_number=phone,
        message=message,
        provider=provider_name,
        status=SMSStatus.PENDING,
    )
    db.session.add(sms_log)
    db.session.commit()

    result = _call_provider(phone, message)
    sms_info = _apply_result(sms_log, result, purchase.staff_id)
    return sms_log, sms_info


def get_sms_log(actor: User, sms_id: str) -> tuple[SMSLog | None, tuple[int, str] | None]:
    sms_log = db.session.get(SMSLog, sms_id)
    if sms_log is None:
        return None, (404, "SMS log not found.")
    if actor.role != UserRole.SUPER_ADMIN and sms_log.shop_id != actor.shop_id:
        return None, (403, "You do not have access to this SMS log.")
    return sms_log, None


def retry_sms(actor: User, sms_log: SMSLog) -> tuple[SMSLog | None, tuple[int, str] | None]:
    if sms_log.status != SMSStatus.FAILED:
        return None, (400, "Only failed SMS can be retried.")

    purchase = db.session.get(Purchase, sms_log.purchase_id)
    if purchase is None:
        return None, (404, "Associated purchase not found.")

    message = sms_log.message
    if not message:
        template = get_active_purchase_template()
        if template is None:
            return None, (400, "No active purchase SMS template configured.")
        message = render_template(template.message, build_sms_context(purchase))
        sms_log.message = message

    if not sms_log.phone_number:
        return None, (400, "Customer has no phone number.")

    result = _call_provider(sms_log.phone_number, message)
    _apply_result(sms_log, result, actor.id, retry=True)
    return sms_log, None


def resolve_pending_sms(actor: User, sms_log: SMSLog) -> tuple[SMSLog | None, tuple[int, str] | None]:
    """Safely resolve an orphaned PENDING SMS without resending it.

    A PENDING record is ambiguous: the message may never have been sent, or it
    may have been accepted by the provider right before the process crashed.
    Because GONLINE offers no delivery-status lookup or idempotency, resending
    would risk a duplicate. This marks the record REVIEW (a distinct,
    non-retryable state) so it cannot flow back through the ordinary FAILED
    retry path, which is available to STAFF/MANAGER.

    Restricted to SUPER_ADMIN and gated by a minimum age so an in-flight send
    cannot be resolved prematurely.
    """
    if actor.role != UserRole.SUPER_ADMIN:
        return None, (403, "You do not have permission to perform this action.")
    if sms_log.status != SMSStatus.PENDING:
        return None, (400, "Only pending SMS can be resolved.")

    threshold = int(current_app.config.get("SMS_PENDING_RECOVERY_SECONDS", 60))
    age = 0.0
    created_at = sms_log.created_at
    if created_at is not None:
        # SQLite returns timezone-naive datetimes; all timestamps are stored
        # in UTC, so assume UTC when tzinfo is missing.
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        age = (utcnow() - created_at).total_seconds()
    if age < threshold:
        return None, (400, "SMS is still in progress. Please try again later.")

    sms_log.status = SMSStatus.REVIEW
    sms_log.error_message = (
        "SMS delivery outcome unknown (stale pending); review required."
    )
    add_audit_log(
        actor.id,
        sms_log.shop_id,
        AuditAction.SMS_RECOVERY,
        "SMS",
        sms_log.id,
        f"SMS pending recovery resolved for ...{_mask_phone(sms_log.phone_number)}.",
    )
    db.session.commit()
    return sms_log, None


def list_sms_logs(
    actor: User,
    *,
    shop_id: str | None = None,
    purchase_id: str | None = None,
    purchase_ids: list[str] | None = None,
    customer_id: str | None = None,
    status: str | None = None,
    date_from=None,
    date_to=None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[SMSLog], dict]:
    page = max(1, page)
    per_page = min(max(1, per_page), 100)

    query = SMSLog.query

    if actor.role == UserRole.SUPER_ADMIN:
        if shop_id:
            query = query.filter(SMSLog.shop_id == shop_id)
    else:
        query = query.filter(SMSLog.shop_id == actor.shop_id)

    if purchase_id:
        query = query.filter(SMSLog.purchase_id == purchase_id)
    if purchase_ids:
        query = query.filter(SMSLog.purchase_id.in_(purchase_ids))
    if customer_id:
        query = query.filter(SMSLog.customer_id == customer_id)
    if status:
        query = query.filter(SMSLog.status == status)
    if date_from:
        query = query.filter(SMSLog.created_at >= date_from)
    if date_to:
        query = query.filter(SMSLog.created_at <= date_to)

    total = query.count()
    pages = (total + per_page - 1) // per_page

    logs = (
        query.order_by(SMSLog.created_at.desc(), SMSLog.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    pagination = {"page": page, "per_page": per_page, "total": total, "pages": pages}
    return logs, pagination
