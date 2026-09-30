import pytest

from app.models import AuditLog, Customer, Purchase, SMSLog, SMSStatus, UserRole
from app.services.audit_service import AuditAction
from app.services.sms import (
    MockSMSProvider,
    ProviderNotImplementedError,
    ProviderResult,
    get_sms_provider,
)
from app.services.template_service import (
    PURCHASE_THANK_YOU,
    get_active_purchase_template,
    render_template,
)
from tests.helpers import (
    auth_header,
    get_token,
    make_customer,
    make_purchase,
    make_shop,
    make_sms_log,
    make_template,
    make_user,
    super_admin_token,
)


def _payload(shop_id=None, phone="0240000000", product="Rice", amount=150.00):
    p = {"customer": {"name": "John", "phone": phone}, "product": product, "amount": amount}
    if shop_id:
        p["shop_id"] = shop_id
    return p


def _post_purchase(client, token, payload):
    return client.post("/api/purchases", headers=auth_header(token), json=payload)


# --- provider ---


def test_mock_provider_sends_successfully():
    result = MockSMSProvider().send_sms("233240000000", "Hello")
    assert result.success is True
    assert result.error_message is None


def test_mock_provider_returns_message_id():
    result = MockSMSProvider().send_sms("233240000000", "Hello")
    assert result.provider_message_id.startswith("mock-message-")


def test_mock_provider_can_simulate_failure():
    result = MockSMSProvider(fail=True).send_sms("233240000000", "Hello")
    assert result.success is False
    assert result.error_message is not None


def test_provider_factory_selects_mock(app):
    app.config["SMS_PROVIDER"] = "mock"
    with app.app_context():
        assert isinstance(get_sms_provider(), MockSMSProvider)


def test_unknown_provider_fails_safely(app):
    app.config["SMS_PROVIDER"] = "nonexistent"
    with app.app_context():
        with pytest.raises(ProviderNotImplementedError):
            get_sms_provider()


# --- template ---


def test_active_purchase_template_selected(session):
    inactive = make_template(session, is_active=False)
    active = make_template(session)
    assert get_active_purchase_template().id == active.id
    assert inactive.is_active is False


def test_template_variables_substituted():
    template = "Hi {{customer_name}}, bought {{product}} for GHS {{amount}} at {{shop_name}}."
    out = render_template(
        template,
        {"customer_name": "John", "product": "Rice", "amount": "150.00", "shop_name": "Main"},
    )
    assert out == "Hi John, bought Rice for GHS 150.00 at Main."


def test_customer_name_substitution():
    assert render_template("Hi {{customer_name}}", {"customer_name": "Ama"}) == "Hi Ama"


def test_shop_name_substitution():
    assert render_template("{{shop_name}}", {"shop_name": "Main"}) == "Main"


def test_product_substitution():
    assert render_template("{{product}}", {"product": "Sugar"}) == "Sugar"


def test_amount_substitution():
    assert render_template("{{amount}}", {"amount": "25.00"}) == "25.00"


def test_unknown_variables_are_not_executed():
    template = "{{__import__('os').system('rm -rf /')}}"
    assert render_template(template, {}) == template


def test_unknown_variable_left_unchanged():
    assert render_template("Hi {{unknown_var}}", {"name": "x"}) == "Hi {{unknown_var}}"


def test_missing_active_template_sms_failed_purchase_ok(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")

    resp = _post_purchase(client, token, _payload(shop.id))
    assert resp.status_code == 201
    assert resp.get_json()["sms"]["status"] == "FAILED"
    assert SMSLog.query.count() == 1
    assert SMSLog.query.first().status == "FAILED"


# --- purchase + sms ---


def test_successful_purchase_creates_sms_log(session, client):
    make_template(session)
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")

    resp = _post_purchase(client, token, _payload(shop.id))
    assert resp.status_code == 201
    assert resp.get_json()["sms"]["status"] == "SENT"
    assert SMSLog.query.count() == 1


def test_successful_sms_sets_status_sent(session, client):
    make_template(session)
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    _post_purchase(client, token, _payload(shop.id))

    log = SMSLog.query.first()
    assert log.status == SMSStatus.SENT


def test_provider_message_id_stored(session, client):
    make_template(session)
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    _post_purchase(client, token, _payload(shop.id))

    log = SMSLog.query.first()
    assert log.provider_message_id.startswith("mock-message-")


def test_sent_at_populated_on_success(session, client):
    make_template(session)
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    _post_purchase(client, token, _payload(shop.id))

    assert SMSLog.query.first().sent_at is not None


def test_failed_provider_sets_failed(session, client, app):
    make_template(session)
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    app.config["SMS_MOCK_FAIL"] = True

    resp = _post_purchase(client, token, _payload(shop.id))
    assert resp.status_code == 201
    assert resp.get_json()["sms"]["status"] == "FAILED"
    assert SMSLog.query.first().status == SMSStatus.FAILED
    assert SMSLog.query.first().error_message is not None


def test_failed_sms_does_not_rollback_purchase(session, client, app):
    make_template(session)
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    app.config["SMS_MOCK_FAIL"] = True

    resp = _post_purchase(client, token, _payload(shop.id))
    assert resp.status_code == 201
    assert Purchase.query.count() == 1
    assert Customer.query.count() == 1
    assert SMSLog.query.count() == 1


def test_purchase_endpoint_returns_success_even_when_sms_fails(session, client, app):
    make_template(session)
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    app.config["SMS_MOCK_FAIL"] = True

    resp = _post_purchase(client, token, _payload(shop.id))
    assert resp.status_code == 201
    assert resp.get_json()["purchase"]["product"] == "Rice"
    assert resp.get_json()["sms"]["status"] == "FAILED"


def test_sms_log_created_pending_before_send(session, app, monkeypatch):
    make_template(session)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    purchase = make_purchase(session, shop, staff, customer)

    from app.services import sms_service as sms_module

    captured = {}

    class FakeProvider:
        name = "fake"

        def send_sms(self, phone, message, sender_id=None):
            captured["status_at_send"] = SMSLog.query.first().status
            return ProviderResult(success=True, provider_message_id="fake-1")

    monkeypatch.setattr(sms_module, "get_sms_provider", lambda: FakeProvider())

    sms_log, info = sms_module.send_purchase_sms(purchase)
    assert captured["status_at_send"] == SMSStatus.PENDING
    assert sms_log.status == SMSStatus.SENT


# --- sms log listing/detail ---


def test_super_admin_can_list_sms_logs(session, client):
    make_template(session)
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    _post_purchase(client, token, _payload(shop.id))

    resp = client.get("/api/sms", headers=auth_header(token))
    assert resp.status_code == 200
    assert len(resp.get_json()["sms_logs"]) == 1


def test_manager_sees_only_own_shop_sms_logs(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff_a = make_user(session, UserRole.STAFF, "staffa@example.com", shop=shop_a)
    staff_b = make_user(session, UserRole.STAFF, "staffb@example.com", shop=shop_b)
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)
    customer = make_customer(session, "John", "233240000000")
    pa = make_purchase(session, shop_a, staff_a, customer)
    pb = make_purchase(session, shop_b, staff_b, customer)
    make_sms_log(session, shop_a, pa, customer)
    make_sms_log(session, shop_b, pb, customer)

    token = get_token(client, "mgr@example.com")
    resp = client.get("/api/sms", headers=auth_header(token))
    logs = resp.get_json()["sms_logs"]
    assert len(logs) == 1
    assert logs[0]["shop_id"] == shop_a.id


def test_cross_shop_sms_access_rejected(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff_a = make_user(session, UserRole.STAFF, "staffa@example.com", shop=shop_a)
    staff_b = make_user(session, UserRole.STAFF, "staffb@example.com", shop=shop_b)
    customer = make_customer(session, "John", "233240000000")
    pb = make_purchase(session, shop_b, staff_b, customer)
    sms = make_sms_log(session, shop_b, pb, customer)

    token = get_token(client, "staffa@example.com")
    resp = client.get(f"/api/sms/{sms.id}", headers=auth_header(token))
    assert resp.status_code == 403


def test_sms_detail_works(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    purchase = make_purchase(session, shop, staff, customer)
    sms = make_sms_log(session, shop, purchase, customer)

    resp = client.get(f"/api/sms/{sms.id}", headers=auth_header(token))
    assert resp.status_code == 200
    body = resp.get_json()["sms"]
    assert body["status"] == SMSStatus.FAILED
    assert "api_key" not in body


def test_sms_pagination(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    for i in range(3):
        p = make_purchase(session, shop, staff, customer, product=f"Item {i}")
        make_sms_log(session, shop, p, customer)

    resp = client.get("/api/sms?page=1&per_page=2", headers=auth_header(token))
    body = resp.get_json()
    assert len(body["sms_logs"]) == 2
    assert body["pagination"]["total"] == 3
    assert body["pagination"]["pages"] == 2


def test_sms_status_filter(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    p1 = make_purchase(session, shop, staff, customer)
    p2 = make_purchase(session, shop, staff, customer, product="Oil")
    make_sms_log(session, shop, p1, customer, status=SMSStatus.SENT)
    make_sms_log(session, shop, p2, customer, status=SMSStatus.FAILED)

    resp = client.get("/api/sms?status=SENT", headers=auth_header(token))
    logs = resp.get_json()["sms_logs"]
    assert len(logs) == 1
    assert logs[0]["status"] == SMSStatus.SENT


def test_sms_purchase_filter(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    p1 = make_purchase(session, shop, staff, customer)
    p2 = make_purchase(session, shop, staff, customer, product="Oil")
    make_sms_log(session, shop, p1, customer)
    make_sms_log(session, shop, p2, customer)

    resp = client.get(f"/api/sms?purchase_id={p1.id}", headers=auth_header(token))
    logs = resp.get_json()["sms_logs"]
    assert len(logs) == 1
    assert logs[0]["purchase_id"] == p1.id


def test_sms_date_filter(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    p = make_purchase(session, shop, staff, customer)
    make_sms_log(session, shop, p, customer)

    resp = client.get("/api/sms?date_from=2000-01-01", headers=auth_header(token))
    assert len(resp.get_json()["sms_logs"]) == 1

    resp = client.get("/api/sms?date_from=2999-01-01", headers=auth_header(token))
    assert len(resp.get_json()["sms_logs"]) == 0


# --- retry ---


def test_failed_sms_can_be_retried(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    purchase = make_purchase(session, shop, staff, customer)
    sms = make_sms_log(session, shop, purchase, customer, status=SMSStatus.FAILED)

    resp = client.post(f"/api/sms/{sms.id}/retry", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.get_json()["sms"]["status"] == SMSStatus.SENT
    assert SMSLog.query.first().status == SMSStatus.SENT


def test_failed_retry_remains_failed(session, client, app):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    purchase = make_purchase(session, shop, staff, customer)
    sms = make_sms_log(session, shop, purchase, customer, status=SMSStatus.FAILED)
    app.config["SMS_MOCK_FAIL"] = True

    resp = client.post(f"/api/sms/{sms.id}/retry", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.get_json()["sms"]["status"] == SMSStatus.FAILED


def test_sent_sms_cannot_be_retried(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    purchase = make_purchase(session, shop, staff, customer)
    sms = make_sms_log(session, shop, purchase, customer, status=SMSStatus.SENT)

    resp = client.post(f"/api/sms/{sms.id}/retry", headers=auth_header(token))
    assert resp.status_code == 400


def test_cross_shop_retry_rejected(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    make_user(session, UserRole.STAFF, "staffa@example.com", shop=shop_a)
    staff_b = make_user(session, UserRole.STAFF, "staffb@example.com", shop=shop_b)
    customer = make_customer(session, "John", "233240000000")
    pb = make_purchase(session, shop_b, staff_b, customer)
    sms = make_sms_log(session, shop_b, pb, customer, status=SMSStatus.FAILED)

    token = get_token(client, "staffa@example.com")
    resp = client.post(f"/api/sms/{sms.id}/retry", headers=auth_header(token))
    assert resp.status_code == 403


def test_retry_does_not_create_another_purchase(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    purchase = make_purchase(session, shop, staff, customer)
    sms = make_sms_log(session, shop, purchase, customer, status=SMSStatus.FAILED)

    client.post(f"/api/sms/{sms.id}/retry", headers=auth_header(token))
    assert Purchase.query.count() == 1


# --- security ---


def test_missing_jwt_rejected(client):
    assert client.get("/api/sms").status_code == 401
    assert client.get("/api/sms/xyz").status_code == 401


def test_invalid_jwt_rejected(client):
    assert client.get("/api/sms", headers=auth_header("bad-token")).status_code == 401


def test_shop_id_filter_cannot_escape_authorization(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff_a = make_user(session, UserRole.STAFF, "staffa@example.com", shop=shop_a)
    staff_b = make_user(session, UserRole.STAFF, "staffb@example.com", shop=shop_b)
    customer = make_customer(session, "John", "233240000000")
    pa = make_purchase(session, shop_a, staff_a, customer)
    pb = make_purchase(session, shop_b, staff_b, customer)
    make_sms_log(session, shop_a, pa, customer)
    make_sms_log(session, shop_b, pb, customer)

    token = get_token(client, "staffa@example.com")
    resp = client.get(f"/api/sms?shop_id={shop_b.id}", headers=auth_header(token))
    logs = resp.get_json()["sms_logs"]
    assert len(logs) == 1
    assert logs[0]["shop_id"] == shop_a.id


def test_provider_credentials_never_in_responses(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    purchase = make_purchase(session, shop, staff, customer)
    sms = make_sms_log(session, shop, purchase, customer)

    resp = client.get(f"/api/sms/{sms.id}", headers=auth_header(token))
    body = resp.get_json()["sms"]
    assert "api_key" not in body
    assert "api_secret" not in body
    assert "password" not in body
    assert "secret" not in body


def test_api_keys_never_in_audit_log(session, client, app):
    make_template(session)
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    app.config["SMS_API_KEY"] = "super-secret-key"
    _post_purchase(client, token, _payload(shop.id))

    for log in AuditLog.query.all():
        text = (log.description or "") + (log.action or "")
        assert "super-secret-key" not in text
        assert "eyJ" not in text


# --- additional coverage ---


def test_no_active_template_returns_none(session):
    assert get_active_purchase_template() is None


def test_inactive_template_not_selected(session):
    make_template(session, is_active=False)
    assert get_active_purchase_template() is None


def test_staff_sees_only_own_shop_sms_logs(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff_a = make_user(session, UserRole.STAFF, "staffa@example.com", shop=shop_a)
    staff_b = make_user(session, UserRole.STAFF, "staffb@example.com", shop=shop_b)
    customer = make_customer(session, "John", "233240000000")
    pa = make_purchase(session, shop_a, staff_a, customer)
    pb = make_purchase(session, shop_b, staff_b, customer)
    make_sms_log(session, shop_a, pa, customer)
    make_sms_log(session, shop_b, pb, customer)

    token = get_token(client, "staffa@example.com")
    resp = client.get("/api/sms", headers=auth_header(token))
    logs = resp.get_json()["sms_logs"]
    assert len(logs) == 1
    assert logs[0]["shop_id"] == shop_a.id


def test_sms_phone_stored_normalized(session, client):
    make_template(session)
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")

    _post_purchase(client, token, _payload(shop.id, phone="+233240000000"))
    assert SMSLog.query.first().phone_number == "233240000000"


def test_retry_rerenders_message_when_empty(session, client):
    make_template(session, message="Thanks {{customer_name}} for buying {{product}}.")
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    purchase = make_purchase(session, shop, staff, customer)
    sms = make_sms_log(session, shop, purchase, customer, status=SMSStatus.FAILED, message="")

    resp = client.post(f"/api/sms/{sms.id}/retry", headers=auth_header(token))
    assert resp.status_code == 200
    refreshed = SMSLog.query.first()
    assert refreshed.status == SMSStatus.SENT
    assert "John" in refreshed.message
