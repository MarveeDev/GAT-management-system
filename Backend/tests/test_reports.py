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


def _summary(client, token, query=""):
    return client.get(f"/api/reports/summary{query}", headers=auth_header(token))


def _shop_with_staff_and_customer(session, shop_name, staff_email, phone):
    shop = make_shop(session, shop_name)
    staff = make_user(session, UserRole.STAFF, staff_email, shop=shop)
    customer = make_customer(session, "Customer", phone)
    return shop, staff, customer


# --- authentication / role ---


def test_summary_requires_auth(client):
    assert client.get("/api/reports/summary").status_code == 401


# --- super admin scope ---


def test_super_admin_summary_across_shops(session, client):
    token = super_admin_token(session, client)
    shop_a, staff_a, customer_a = _shop_with_staff_and_customer(
        session, "Shop A", "staffa@example.com", "233240000001"
    )
    shop_b, staff_b, customer_b = _shop_with_staff_and_customer(
        session, "Shop B", "staffb@example.com", "233240000002"
    )
    make_purchase(session, shop_a, staff_a, customer_a, amount=Decimal("100.00"))
    make_purchase(session, shop_b, staff_b, customer_b, amount=Decimal("200.00"))

    resp = _summary(client, token)
    assert resp.status_code == 200
    summary = resp.get_json()["summary"]
    assert summary["total_purchases"] == 2
    assert summary["total_sales"] == "300.00"


def test_super_admin_summary_shop_filter(session, client):
    token = super_admin_token(session, client)
    shop_a, staff_a, customer_a = _shop_with_staff_and_customer(
        session, "Shop A", "staffa@example.com", "233240000001"
    )
    shop_b, staff_b, customer_b = _shop_with_staff_and_customer(
        session, "Shop B", "staffb@example.com", "233240000002"
    )
    make_purchase(session, shop_a, staff_a, customer_a, amount=Decimal("100.00"))
    make_purchase(session, shop_b, staff_b, customer_b, amount=Decimal("200.00"))

    resp = _summary(client, token, f"?shop_id={shop_a.id}")
    assert resp.status_code == 200
    summary = resp.get_json()["summary"]
    assert summary["total_purchases"] == 1
    assert summary["total_sales"] == "100.00"


# --- manager scope ---


def test_manager_summary_own_shop(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)
    staff_a = make_user(session, UserRole.STAFF, "staffa@example.com", shop=shop_a)
    staff_b = make_user(session, UserRole.STAFF, "staffb@example.com", shop=shop_b)
    customer = make_customer(session, "Customer", "233240000001")
    make_purchase(session, shop_a, staff_a, customer, amount=Decimal("100.00"))
    make_purchase(session, shop_b, staff_b, customer, amount=Decimal("200.00"))

    token = get_token(client, "mgr@example.com")
    resp = _summary(client, token)
    assert resp.status_code == 200
    summary = resp.get_json()["summary"]
    assert summary["total_purchases"] == 1
    assert summary["total_sales"] == "100.00"


def test_manager_summary_cross_shop_denied(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)
    token = get_token(client, "mgr@example.com")

    resp = _summary(client, token, f"?shop_id={shop_b.id}")
    assert resp.status_code == 403


# --- staff scope ---


def test_staff_summary_cross_shop_denied(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop_a)
    token = get_token(client, "staff@example.com")

    assert _summary(client, token).status_code == 200  # own shop allowed
    assert _summary(client, token, f"?shop_id={shop_b.id}").status_code == 403


# --- date range ---


def test_summary_date_filter(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Customer", "233240000001")
    base = datetime(2026, 9, 1, 12, 0, 0)
    make_purchase(
        session, shop, staff, customer, created_at=base, amount=Decimal("100.00")
    )
    make_purchase(
        session,
        shop,
        staff,
        customer,
        product="Oil",
        created_at=base + timedelta(days=10),
        amount=Decimal("200.00"),
    )

    resp = _summary(client, token, "?date_from=2026-09-05&date_to=2026-09-20")
    assert resp.status_code == 200
    summary = resp.get_json()["summary"]
    assert summary["total_purchases"] == 1
    assert summary["total_sales"] == "200.00"


def test_summary_invalid_date_range(session, client):
    token = super_admin_token(session, client)
    resp = _summary(client, token, "?date_from=2026-10-01&date_to=2026-09-01")
    assert resp.status_code == 400


def test_summary_invalid_preset(session, client):
    token = super_admin_token(session, client)
    resp = _summary(client, token, "?preset=bogus")
    assert resp.status_code == 400


def test_summary_preset_conflicts_with_dates(session, client):
    token = super_admin_token(session, client)
    resp = _summary(client, token, "?preset=today&date_from=2026-09-01")
    assert resp.status_code == 400


def test_summary_nonexistent_shop(session, client):
    token = super_admin_token(session, client)
    resp = _summary(client, token, "?shop_id=nonexistent")
    assert resp.status_code == 404


# --- metrics ---


def test_summary_unique_customers(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer_a = make_customer(session, "A", "233240000001")
    customer_b = make_customer(session, "B", "233240000002")
    make_purchase(session, shop, staff, customer_a, product="Rice")
    make_purchase(session, shop, staff, customer_a, product="Oil")
    make_purchase(session, shop, staff, customer_b, product="Sugar")

    resp = _summary(client, token)
    summary = resp.get_json()["summary"]
    assert summary["unique_customers"] == 2


def test_summary_money_aggregation(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Customer", "233240000001")
    make_purchase(session, shop, staff, customer, amount=Decimal("100.00"))
    make_purchase(session, shop, staff, customer, product="Oil", amount=Decimal("250.00"))
    make_purchase(session, shop, staff, customer, product="Sugar", amount=Decimal("150.00"))

    summary = _summary(client, token).get_json()["summary"]
    assert summary["total_sales"] == "500.00"
    assert summary["average_purchase_value"] == "166.67"


def test_summary_sms_counts(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Customer", "233240000001")
    p1 = make_purchase(session, shop, staff, customer)
    p2 = make_purchase(session, shop, staff, customer, product="Oil")
    p3 = make_purchase(session, shop, staff, customer, product="Sugar")
    p4 = make_purchase(session, shop, staff, customer, product="Salt")
    make_sms_log(session, shop, p1, customer, status=SMSStatus.SENT)
    make_sms_log(session, shop, p2, customer, status=SMSStatus.SENT)
    make_sms_log(session, shop, p3, customer, status=SMSStatus.FAILED)
    make_sms_log(session, shop, p4, customer, status=SMSStatus.PENDING)

    summary = _summary(client, token).get_json()["summary"]
    assert summary["sms_sent"] == 2
    assert summary["sms_failed"] == 1
    assert summary["sms_pending"] == 1
