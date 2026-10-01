import json
from datetime import datetime, timedelta
from decimal import Decimal

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


def _shops_report(client, token, query=""):
    return client.get(f"/api/reports/shops{query}", headers=auth_header(token))


def _shop_by_name(data, name):
    for entry in data["shops"]:
        if entry["shop"]["name"] == name:
            return entry
    return None


def _sms(session, shop, staff, customer, status=SMSStatus.SENT, created_at=None):
    purchase = make_purchase(session, shop, staff, customer)
    return make_sms_log(
        session, shop, purchase, customer, status=status, created_at=created_at
    )


# --- authentication ---


def test_shops_requires_auth(client):
    assert client.get("/api/reports/shops").status_code == 401


# --- scope ---


def test_super_admin_all_shops(session, client):
    token = super_admin_token(session, client)
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    shop_c = make_shop(session, "Shop C")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop_a)
    customer = make_customer(session, "Customer", "233240000001")
    make_purchase(session, shop_a, staff, customer, amount=Decimal("100.00"))
    make_purchase(session, shop_b, staff, customer, amount=Decimal("200.00"))

    data = _shops_report(client, token).get_json()
    names = [entry["shop"]["name"] for entry in data["shops"]]
    assert names == ["Shop A", "Shop B", "Shop C"]


def test_super_admin_shop_filter(session, client):
    token = super_admin_token(session, client)
    shop_a = make_shop(session, "Shop A")
    make_shop(session, "Shop B")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop_a)
    customer = make_customer(session, "Customer", "233240000001")
    make_purchase(session, shop_a, staff, customer, amount=Decimal("100.00"))

    data = _shops_report(client, token, f"?shop_id={shop_a.id}").get_json()
    assert len(data["shops"]) == 1
    assert data["shops"][0]["shop"]["id"] == shop_a.id


def test_manager_own_shop(session, client):
    shop_a = make_shop(session, "Shop A")
    make_shop(session, "Shop B")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)
    token = get_token(client, "mgr@example.com")

    data = _shops_report(client, token).get_json()
    assert len(data["shops"]) == 1
    assert data["shops"][0]["shop"]["id"] == shop_a.id


def test_manager_cross_shop_denied(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)
    token = get_token(client, "mgr@example.com")

    assert _shops_report(client, token, f"?shop_id={shop_b.id}").status_code == 403


def test_staff_own_shop(session, client):
    shop_a = make_shop(session, "Shop A")
    make_shop(session, "Shop B")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop_a)
    token = get_token(client, "staff@example.com")

    data = _shops_report(client, token).get_json()
    assert len(data["shops"]) == 1
    assert data["shops"][0]["shop"]["id"] == shop_a.id


def test_staff_cross_shop_denied(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop_a)
    token = get_token(client, "staff@example.com")

    assert _shops_report(client, token, f"?shop_id={shop_b.id}").status_code == 403


# --- purchase metrics ---


def test_shop_purchase_metrics(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Customer", "233240000001")
    make_purchase(session, shop, staff, customer, amount=Decimal("100.00"))
    make_purchase(session, shop, staff, customer, product="Oil", amount=Decimal("250.00"))
    make_purchase(session, shop, staff, customer, product="Sugar", amount=Decimal("150.00"))

    entry = _shop_by_name(_shops_report(client, token).get_json(), "Shop A")
    m = entry["metrics"]
    assert m["total_purchases"] == 3
    assert m["total_sales"] == "500.00"
    assert m["average_purchase_value"] == "166.67"


def test_shop_unique_customers(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer_a = make_customer(session, "A", "233240000001")
    customer_b = make_customer(session, "B", "233240000002")
    make_purchase(session, shop, staff, customer_a, product="Rice")
    make_purchase(session, shop, staff, customer_a, product="Oil")
    make_purchase(session, shop, staff, customer_b, product="Sugar")

    entry = _shop_by_name(_shops_report(client, token).get_json(), "Shop A")
    assert entry["metrics"]["unique_customers"] == 2


# --- sms metrics ---


def test_shop_sms_metrics(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Customer", "233240000001")
    _sms(session, shop, staff, customer, status=SMSStatus.SENT)
    _sms(session, shop, staff, customer, status=SMSStatus.SENT)
    _sms(session, shop, staff, customer, status=SMSStatus.FAILED)
    _sms(session, shop, staff, customer, status=SMSStatus.PENDING)

    entry = _shop_by_name(_shops_report(client, token).get_json(), "Shop A")
    m = entry["metrics"]
    assert m["sms_sent"] == 2
    assert m["sms_failed"] == 1
    assert m["sms_pending"] == 1
    assert m["sms_success_rate"] == "50.00"


def test_shop_zero_sms_success_rate(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Customer", "233240000001")
    make_purchase(session, shop, staff, customer)

    entry = _shop_by_name(_shops_report(client, token).get_json(), "Shop A")
    assert entry["metrics"]["sms_success_rate"] == "0.00"


# --- empty shop ---


def test_empty_shop_included(session, client):
    token = super_admin_token(session, client)
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop_a)
    customer = make_customer(session, "Customer", "233240000001")
    make_purchase(session, shop_a, staff, customer, amount=Decimal("100.00"))

    entry = _shop_by_name(_shops_report(client, token).get_json(), "Shop B")
    assert entry is not None
    m = entry["metrics"]
    assert m["total_purchases"] == 0
    assert m["total_sales"] == "0.00"
    assert m["average_purchase_value"] == "0.00"
    assert m["unique_customers"] == 0
    assert m["sms_sent"] == 0
    assert m["sms_failed"] == 0
    assert m["sms_pending"] == 0


# --- overall totals ---


def test_overall_totals_unique_customers(session, client):
    token = super_admin_token(session, client)
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff_a = make_user(session, UserRole.STAFF, "staffa@example.com", shop=shop_a)
    staff_b = make_user(session, UserRole.STAFF, "staffb@example.com", shop=shop_b)
    customer = make_customer(session, "Shared", "233240000001")
    make_purchase(session, shop_a, staff_a, customer, amount=Decimal("100.00"))
    make_purchase(session, shop_b, staff_b, customer, amount=Decimal("200.00"))

    data = _shops_report(client, token).get_json()
    totals = data["totals"]
    assert totals["total_purchases"] == 2
    assert totals["total_sales"] == "300.00"
    assert totals["unique_customers"] == 1


# --- date range ---


def test_shop_date_range(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Customer", "233240000001")
    base = datetime(2026, 9, 1, 12, 0, 0)
    make_purchase(session, shop, staff, customer, created_at=base, amount=Decimal("100.00"))
    make_purchase(
        session,
        shop,
        staff,
        customer,
        product="Oil",
        created_at=base + timedelta(days=10),
        amount=Decimal("200.00"),
    )
    make_purchase(
        session,
        shop,
        staff,
        customer,
        product="Sugar",
        created_at=base + timedelta(days=30),
        amount=Decimal("300.00"),
    )

    data = _shops_report(
        client, token, "?date_from=2026-09-05&date_to=2026-09-20"
    ).get_json()
    m = _shop_by_name(data, "Shop A")["metrics"]
    assert m["total_purchases"] == 1
    assert m["total_sales"] == "200.00"


def test_shop_filter_and_date_range(session, client):
    token = super_admin_token(session, client)
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop_a)
    customer = make_customer(session, "Customer", "233240000001")
    base = datetime(2026, 9, 1, 12, 0, 0)
    make_purchase(session, shop_a, staff, customer, created_at=base + timedelta(days=10), amount=Decimal("100.00"))
    make_purchase(session, shop_b, staff, customer, created_at=base + timedelta(days=10), amount=Decimal("200.00"))

    data = _shops_report(
        client, token, f"?shop_id={shop_a.id}&date_from=2026-09-05&date_to=2026-09-20"
    ).get_json()
    assert len(data["shops"]) == 1
    m = data["shops"][0]["metrics"]
    assert m["total_purchases"] == 1
    assert m["total_sales"] == "100.00"


# --- errors / security ---


def test_shops_invalid_date_and_preset(session, client):
    token = super_admin_token(session, client)
    assert _shops_report(client, token, "?preset=bogus").status_code == 400
    assert _shops_report(
        client, token, "?date_from=2026-10-01&date_to=2026-09-01"
    ).status_code == 400
    assert _shops_report(
        client, token, "?preset=today&date_from=2026-09-01"
    ).status_code == 400


def test_shops_nonexistent_shop(session, client):
    token = super_admin_token(session, client)
    assert _shops_report(client, token, "?shop_id=nonexistent").status_code == 404


def test_shops_no_secrets(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Customer", "233240000001")
    make_purchase(session, shop, staff, customer)

    text = json.dumps(_shops_report(client, token).get_json())
    assert "password" not in text
    assert "token" not in text
    assert "secret" not in text
    assert "api_key" not in text
