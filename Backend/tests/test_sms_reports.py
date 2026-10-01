import json
from datetime import datetime, timedelta

from app.models import SMSStatus, UserRole
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


def _sms_report(client, token, query=""):
    return client.get(f"/api/reports/sms{query}", headers=auth_header(token))


def _setup(session):
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Customer", "233240000001")
    return shop, staff, customer


def _sms(session, shop, staff, customer, status=SMSStatus.SENT, created_at=None, error_message=None):
    purchase = make_purchase(session, shop, staff, customer)
    return make_sms_log(
        session,
        shop,
        purchase,
        customer,
        status=status,
        created_at=created_at,
        error_message=error_message,
    )


# --- authentication ---


def test_sms_requires_auth(client):
    assert client.get("/api/reports/sms").status_code == 401


# --- scope ---


def test_super_admin_sms_across_shops(session, client):
    token = super_admin_token(session, client)
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff_a = make_user(session, UserRole.STAFF, "staffa@example.com", shop=shop_a)
    staff_b = make_user(session, UserRole.STAFF, "staffb@example.com", shop=shop_b)
    customer_a = make_customer(session, "A", "233240000001")
    customer_b = make_customer(session, "B", "233240000002")
    _sms(session, shop_a, staff_a, customer_a, status=SMSStatus.SENT)
    _sms(session, shop_b, staff_b, customer_b, status=SMSStatus.FAILED)

    data = _sms_report(client, token).get_json()
    assert data["summary"]["total_sms"] == 2
    assert len(data["sms"]) == 2


def test_super_admin_sms_shop_filter(session, client):
    token = super_admin_token(session, client)
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff_a = make_user(session, UserRole.STAFF, "staffa@example.com", shop=shop_a)
    staff_b = make_user(session, UserRole.STAFF, "staffb@example.com", shop=shop_b)
    customer_a = make_customer(session, "A", "233240000001")
    customer_b = make_customer(session, "B", "233240000002")
    _sms(session, shop_a, staff_a, customer_a, status=SMSStatus.SENT)
    _sms(session, shop_b, staff_b, customer_b, status=SMSStatus.FAILED)

    data = _sms_report(client, token, f"?shop_id={shop_a.id}").get_json()
    assert data["summary"]["total_sms"] == 1
    assert data["sms"][0]["shop"]["id"] == shop_a.id


def test_manager_sms_own_shop(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)
    staff_a = make_user(session, UserRole.STAFF, "staffa@example.com", shop=shop_a)
    staff_b = make_user(session, UserRole.STAFF, "staffb@example.com", shop=shop_b)
    customer = make_customer(session, "Customer", "233240000001")
    _sms(session, shop_a, staff_a, customer, status=SMSStatus.SENT)
    _sms(session, shop_b, staff_b, customer, status=SMSStatus.SENT)

    token = get_token(client, "mgr@example.com")
    data = _sms_report(client, token).get_json()
    assert data["summary"]["total_sms"] == 1
    assert data["sms"][0]["shop"]["id"] == shop_a.id


def test_manager_sms_cross_shop_denied(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)
    token = get_token(client, "mgr@example.com")

    assert _sms_report(client, token, f"?shop_id={shop_b.id}").status_code == 403


def test_staff_sms_cross_shop_denied(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop_a)
    token = get_token(client, "staff@example.com")

    assert _sms_report(client, token).status_code == 200  # own shop
    assert _sms_report(client, token, f"?shop_id={shop_b.id}").status_code == 403


# --- date range ---


def test_sms_date_filter(session, client):
    token = super_admin_token(session, client)
    shop, staff, customer = _setup(session)
    base = datetime(2026, 9, 1, 12, 0, 0)
    _sms(session, shop, staff, customer, created_at=base)
    _sms(session, shop, staff, customer, created_at=base + timedelta(days=10))
    _sms(session, shop, staff, customer, created_at=base + timedelta(days=30))

    data = _sms_report(
        client, token, "?date_from=2026-09-05&date_to=2026-09-20"
    ).get_json()
    assert data["summary"]["total_sms"] == 1


# --- status counts / success rate ---


def test_sms_status_counts(session, client):
    token = super_admin_token(session, client)
    shop, staff, customer = _setup(session)
    _sms(session, shop, staff, customer, status=SMSStatus.SENT)
    _sms(session, shop, staff, customer, status=SMSStatus.SENT)
    _sms(session, shop, staff, customer, status=SMSStatus.FAILED)
    _sms(session, shop, staff, customer, status=SMSStatus.PENDING)

    summary = _sms_report(client, token).get_json()["summary"]
    assert summary["total_sms"] == 4
    assert summary["sms_sent"] == 2
    assert summary["sms_failed"] == 1
    assert summary["sms_pending"] == 1
    assert summary["success_rate"] == "50.00"


def test_sms_zero_records(session, client):
    token = super_admin_token(session, client)
    summary = _sms_report(client, token).get_json()["summary"]
    assert summary["total_sms"] == 0
    assert summary["sms_sent"] == 0
    assert summary["sms_failed"] == 0
    assert summary["sms_pending"] == 0
    assert summary["success_rate"] == "0.00"


# --- pagination ---


def test_sms_pagination(session, client):
    token = super_admin_token(session, client)
    shop, staff, customer = _setup(session)
    for _ in range(5):
        _sms(session, shop, staff, customer)

    page1 = _sms_report(client, token, "?page=1&per_page=2").get_json()
    assert len(page1["sms"]) == 2
    assert page1["pagination"]["total"] == 5
    assert page1["pagination"]["pages"] == 3

    page2 = _sms_report(client, token, "?page=2&per_page=2").get_json()
    assert len(page2["sms"]) == 2

    page3 = _sms_report(client, token, "?page=3&per_page=2").get_json()
    assert len(page3["sms"]) == 1


def test_sms_summary_not_page_limited(session, client):
    token = super_admin_token(session, client)
    shop, staff, customer = _setup(session)
    for _ in range(5):
        _sms(session, shop, staff, customer, status=SMSStatus.SENT)

    data = _sms_report(client, token, "?per_page=2").get_json()
    assert len(data["sms"]) == 2
    assert data["summary"]["total_sms"] == 5
    assert data["summary"]["sms_sent"] == 5


# --- record information ---


def test_sms_customer_data(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Kofi Mensah", "0241234567")
    _sms(session, shop, staff, customer)

    row = _sms_report(client, token).get_json()["sms"][0]
    assert row["customer"]["id"] == customer.id
    assert row["customer"]["name"] == "Kofi Mensah"
    assert row["customer"]["phone"] == "0241234567"


def test_sms_shop_data(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Customer", "233240000001")
    _sms(session, shop, staff, customer)

    row = _sms_report(client, token).get_json()["sms"][0]
    assert row["shop"]["id"] == shop.id
    assert row["shop"]["name"] == "Shop A"


def test_sms_purchase_id(session, client):
    token = super_admin_token(session, client)
    shop, staff, customer = _setup(session)
    purchase = make_purchase(session, shop, staff, customer)
    make_sms_log(session, shop, purchase, customer, status=SMSStatus.SENT)

    row = _sms_report(client, token).get_json()["sms"][0]
    assert row["purchase_id"] == purchase.id


def test_sms_failed_error(session, client):
    token = super_admin_token(session, client)
    shop, staff, customer = _setup(session)
    _sms(
        session,
        shop,
        staff,
        customer,
        status=SMSStatus.FAILED,
        error_message="Provider request failed",
    )

    row = _sms_report(client, token).get_json()["sms"][0]
    assert row["status"] == "FAILED"
    assert row["error_message"] == "Provider request failed"


def test_sms_no_secrets(session, client):
    token = super_admin_token(session, client)
    shop, staff, customer = _setup(session)
    _sms(session, shop, staff, customer, status=SMSStatus.SENT)

    text = json.dumps(_sms_report(client, token).get_json())
    assert "password" not in text
    assert "token" not in text
    assert "secret" not in text
    assert "api_key" not in text


# --- ordering ---


def test_sms_newest_first(session, client):
    token = super_admin_token(session, client)
    shop, staff, customer = _setup(session)
    base = datetime(2026, 9, 1, 12, 0, 0)
    _sms(session, shop, staff, customer, created_at=base)
    _sms(session, shop, staff, customer, created_at=base + timedelta(days=5))

    rows = _sms_report(
        client, token, "?date_from=2026-09-01&date_to=2026-09-30"
    ).get_json()["sms"]
    assert rows[0]["date"] > rows[1]["date"]


# --- invalid input ---


def test_sms_invalid_pagination(session, client):
    token = super_admin_token(session, client)
    assert _sms_report(client, token, "?page=0").status_code == 400
    assert _sms_report(client, token, "?per_page=0").status_code == 400
    assert _sms_report(client, token, "?per_page=101").status_code == 400
    assert _sms_report(client, token, "?page=abc").status_code == 400
    assert _sms_report(client, token, "?per_page=xyz").status_code == 400


def test_sms_invalid_date_and_preset(session, client):
    token = super_admin_token(session, client)
    assert _sms_report(client, token, "?preset=bogus").status_code == 400
    assert _sms_report(
        client, token, "?date_from=2026-10-01&date_to=2026-09-01"
    ).status_code == 400
    assert _sms_report(
        client, token, "?preset=today&date_from=2026-09-01"
    ).status_code == 400
