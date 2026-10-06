from datetime import datetime, timedelta, timezone

from app.extensions import db
from app.models import AuditLog, Purchase, SMSLog, SMSStatus, UserRole
from app.services.audit_service import AuditAction
from tests.helpers import (
    auth_header,
    get_token,
    make_customer,
    make_purchase,
    make_shop,
    make_sms_log,
    make_user,
    super_admin_token,
)


def _stale_pending_sms_log(session, shop, staff, customer, age_seconds=600):
    purchase = make_purchase(session, shop, staff, customer)
    created_at = datetime.now(timezone.utc) - timedelta(seconds=age_seconds)
    sms = make_sms_log(
        session,
        shop,
        purchase,
        customer,
        status=SMSStatus.PENDING,
        created_at=created_at,
    )
    return purchase, sms


def test_resolve_requires_auth(client):
    assert client.post("/api/sms/xyz/resolve").status_code == 401


def test_resolve_marks_stale_pending_review_without_resend(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    _, sms = _stale_pending_sms_log(session, shop, staff, customer)

    resp = client.post(f"/api/sms/{sms.id}/resolve", headers=auth_header(token))
    assert resp.status_code == 200
    body = resp.get_json()["sms"]
    assert body["status"] == SMSStatus.REVIEW
    assert body["provider_message_id"] is None


def test_resolve_does_not_call_provider(session, client, monkeypatch):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    _, sms = _stale_pending_sms_log(session, shop, staff, customer)

    from app.services import sms_service

    calls = []
    monkeypatch.setattr(
        sms_service,
        "_call_provider",
        lambda phone, message: calls.append(phone) or (None, None),
    )

    resp = client.post(f"/api/sms/{sms.id}/resolve", headers=auth_header(token))
    assert resp.status_code == 200
    assert calls == []
    assert db.session.get(SMSLog, sms.id).status == SMSStatus.REVIEW


def test_resolve_does_not_create_purchase_or_sms_log(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    _, sms = _stale_pending_sms_log(session, shop, staff, customer)

    resp = client.post(f"/api/sms/{sms.id}/resolve", headers=auth_header(token))
    assert resp.status_code == 200
    assert Purchase.query.count() == 1
    assert SMSLog.query.count() == 1
    assert SMSLog.query.first().id == sms.id


def test_resolve_updates_same_sms_log_and_audits(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    _, sms = _stale_pending_sms_log(session, shop, staff, customer)

    client.post(f"/api/sms/{sms.id}/resolve", headers=auth_header(token))

    assert SMSLog.query.count() == 1
    logs = AuditLog.query.filter_by(action=AuditAction.SMS_RECOVERY).all()
    assert len(logs) == 1
    assert logs[0].entity_id == sms.id


def test_resolve_requires_super_admin(session, client):
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    _, sms = _stale_pending_sms_log(session, shop, staff, customer)

    staff_token = get_token(client, "staff@example.com")
    mgr_token = get_token(client, "mgr@example.com")

    assert (
        client.post(f"/api/sms/{sms.id}/resolve", headers=auth_header(staff_token)).status_code
        == 403
    )
    assert (
        client.post(f"/api/sms/{sms.id}/resolve", headers=auth_header(mgr_token)).status_code
        == 403
    )
    # Record remains untouched.
    assert db.session.get(SMSLog, sms.id).status == SMSStatus.PENDING


def test_resolve_too_recent_pending_rejected(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    _, sms = _stale_pending_sms_log(session, shop, staff, customer, age_seconds=1)

    resp = client.post(f"/api/sms/{sms.id}/resolve", headers=auth_header(token))
    assert resp.status_code == 400
    assert db.session.get(SMSLog, sms.id).status == SMSStatus.PENDING


def test_resolve_non_pending_rejected(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    purchase = make_purchase(session, shop, staff, customer)
    sms = make_sms_log(session, shop, purchase, customer, status=SMSStatus.FAILED)

    resp = client.post(f"/api/sms/{sms.id}/resolve", headers=auth_header(token))
    assert resp.status_code == 400


# --- REVIEW records must not be retried through the ordinary path ----------


def test_review_records_cannot_be_retried(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    _, sms = _stale_pending_sms_log(session, shop, staff, customer)

    assert client.post(f"/api/sms/{sms.id}/resolve", headers=auth_header(token)).status_code == 200

    # Even SUPER_ADMIN cannot retry a REVIEW record through the retry endpoint.
    retry = client.post(f"/api/sms/{sms.id}/retry", headers=auth_header(token))
    assert retry.status_code == 400
    assert db.session.get(SMSLog, sms.id).status == SMSStatus.REVIEW


def test_staff_cannot_retry_review_record(session, client):
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    _, sms = _stale_pending_sms_log(session, shop, staff, customer)
    sms.status = SMSStatus.REVIEW
    db.session.commit()

    token = get_token(client, "staff@example.com")
    resp = client.post(f"/api/sms/{sms.id}/retry", headers=auth_header(token))
    assert resp.status_code == 400
    assert db.session.get(SMSLog, sms.id).status == SMSStatus.REVIEW


def test_manager_cannot_retry_review_record(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop)
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    _, sms = _stale_pending_sms_log(session, shop, staff, customer)
    sms.status = SMSStatus.REVIEW
    db.session.commit()

    token = get_token(client, "mgr@example.com")
    resp = client.post(f"/api/sms/{sms.id}/retry", headers=auth_header(token))
    assert resp.status_code == 400
    assert db.session.get(SMSLog, sms.id).status == SMSStatus.REVIEW


def test_normal_failed_retry_still_works(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    purchase = make_purchase(session, shop, staff, customer)
    sms = make_sms_log(session, shop, purchase, customer, status=SMSStatus.FAILED)

    resp = client.post(f"/api/sms/{sms.id}/retry", headers=auth_header(token))
    assert resp.status_code == 200
    assert db.session.get(SMSLog, sms.id).status == SMSStatus.SENT
