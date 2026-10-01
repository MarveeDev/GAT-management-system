import json
from datetime import datetime, timedelta
from decimal import Decimal

from app.models import UserRole
from tests.helpers import (
    auth_header,
    get_token,
    make_customer,
    make_purchase,
    make_shop,
    make_user,
    super_admin_token,
)


def _staff_report(client, token, query=""):
    return client.get(f"/api/reports/staff{query}", headers=auth_header(token))


def _staff_by_id(data, staff_id):
    for entry in data["staff"]:
        if entry["staff"]["id"] == staff_id:
            return entry
    return None


# --- authentication ---


def test_staff_requires_auth(client):
    assert client.get("/api/reports/staff").status_code == 401


# --- scope / authorization ---


def test_super_admin_all_staff_activity(session, client):
    token = super_admin_token(session, client)
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff_a = make_user(session, UserRole.STAFF, "a@example.com", shop=shop_a)
    staff_b = make_user(session, UserRole.STAFF, "b@example.com", shop=shop_b)
    customer = make_customer(session, "Customer", "233240000001")
    make_purchase(session, shop_a, staff_a, customer, amount=Decimal("100.00"))
    make_purchase(session, shop_b, staff_b, customer, amount=Decimal("200.00"))

    data = _staff_report(client, token).get_json()
    ids = {entry["staff"]["id"] for entry in data["staff"]}
    assert ids == {staff_a.id, staff_b.id}


def test_super_admin_staff_shop_filter(session, client):
    token = super_admin_token(session, client)
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff_a = make_user(session, UserRole.STAFF, "a@example.com", shop=shop_a)
    staff_b = make_user(session, UserRole.STAFF, "b@example.com", shop=shop_b)
    customer = make_customer(session, "Customer", "233240000001")
    make_purchase(session, shop_a, staff_a, customer, amount=Decimal("100.00"))
    make_purchase(session, shop_b, staff_b, customer, amount=Decimal("200.00"))

    data = _staff_report(client, token, f"?shop_id={shop_a.id}").get_json()
    assert [e["staff"]["id"] for e in data["staff"]] == [staff_a.id]
    assert data["totals"]["total_sales"] == "100.00"


def test_manager_own_shop(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)
    staff_a = make_user(session, UserRole.STAFF, "a@example.com", shop=shop_a)
    staff_b = make_user(session, UserRole.STAFF, "b@example.com", shop=shop_b)
    customer = make_customer(session, "Customer", "233240000001")
    make_purchase(session, shop_a, staff_a, customer, amount=Decimal("100.00"))
    make_purchase(session, shop_b, staff_b, customer, amount=Decimal("200.00"))

    token = get_token(client, "mgr@example.com")
    data = _staff_report(client, token).get_json()
    assert [e["staff"]["id"] for e in data["staff"]] == [staff_a.id]


def test_manager_cross_shop_denied(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)
    token = get_token(client, "mgr@example.com")

    assert _staff_report(client, token, f"?shop_id={shop_b.id}").status_code == 403


def test_staff_cross_shop_denied(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop_a)
    token = get_token(client, "staff@example.com")

    assert _staff_report(client, token).status_code == 200  # own shop
    assert _staff_report(client, token, f"?shop_id={shop_b.id}").status_code == 403


# --- metrics ---


def test_staff_total_purchases_and_sales(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Customer", "233240000001")
    make_purchase(session, shop, staff, customer, amount=Decimal("100.00"))
    make_purchase(session, shop, staff, customer, product="Oil", amount=Decimal("250.00"))
    make_purchase(session, shop, staff, customer, product="Sugar", amount=Decimal("150.00"))

    entry = _staff_report(client, token).get_json()["staff"][0]
    assert entry["metrics"]["total_purchases"] == 3
    assert entry["metrics"]["total_sales"] == "500.00"
    assert entry["metrics"]["average_purchase_value"] == "166.67"


def test_staff_grouped_independently(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff_a = make_user(session, UserRole.STAFF, "a@example.com", shop=shop)
    staff_b = make_user(session, UserRole.STAFF, "b@example.com", shop=shop)
    customer = make_customer(session, "Customer", "233240000001")
    make_purchase(session, shop, staff_a, customer)
    make_purchase(session, shop, staff_b, customer)
    make_purchase(session, shop, staff_b, customer, product="Oil")

    data = _staff_report(client, token).get_json()
    assert len(data["staff"]) == 2
    a = _staff_by_id(data, staff_a.id)
    b = _staff_by_id(data, staff_b.id)
    assert a["metrics"]["total_purchases"] == 1
    assert b["metrics"]["total_purchases"] == 2


def test_staff_identity_from_staff_id(session, client):
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Customer", "233240000001")
    make_purchase(session, shop, staff, customer)
    token = get_token(client, "staff@example.com")

    entry = _staff_report(client, token).get_json()["staff"][0]
    assert entry["staff"]["id"] == staff.id
    assert entry["staff"]["name"] == "staff"
    assert entry["staff"]["email"] == "staff@example.com"
    assert entry["staff"]["role"] == "STAFF"


def test_staff_shop_information(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Customer", "233240000001")
    make_purchase(session, shop, staff, customer)

    entry = _staff_report(client, token).get_json()["staff"][0]
    assert entry["shop"]["id"] == shop.id
    assert entry["shop"]["name"] == "Shop A"
    assert entry["shop"]["status"] == "ACTIVE"


def test_staff_no_secrets(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Customer", "233240000001")
    make_purchase(session, shop, staff, customer)

    text = json.dumps(_staff_report(client, token).get_json())
    assert "password" not in text
    assert "token" not in text
    assert "secret" not in text
    assert "api_key" not in text


# --- date range ---


def test_staff_date_filter(session, client):
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

    data = _staff_report(
        client, token, "?date_from=2026-09-05&date_to=2026-09-20"
    ).get_json()
    entry = data["staff"][0]
    assert entry["metrics"]["total_purchases"] == 1
    assert entry["metrics"]["total_sales"] == "200.00"


# --- empty / ordering ---


def test_staff_empty_range(session, client):
    token = super_admin_token(session, client)
    data = _staff_report(client, token).get_json()
    assert data["staff"] == []
    assert data["totals"]["total_purchases"] == 0
    assert data["totals"]["total_sales"] == "0.00"


def test_staff_ordering(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff_low = make_user(session, UserRole.STAFF, "low@example.com", shop=shop, name="Low")
    staff_high = make_user(session, UserRole.STAFF, "high@example.com", shop=shop, name="High")
    customer = make_customer(session, "Customer", "233240000001")
    make_purchase(session, shop, staff_low, customer)
    make_purchase(session, shop, staff_high, customer)
    make_purchase(session, shop, staff_high, customer, product="Oil")
    make_purchase(session, shop, staff_high, customer, product="Sugar")

    ids = [e["staff"]["id"] for e in _staff_report(client, token).get_json()["staff"]]
    assert ids == [staff_high.id, staff_low.id]


def test_staff_ordering_name_tiebreak(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    zed = make_user(session, UserRole.STAFF, "zed@example.com", shop=shop, name="Zed")
    amy = make_user(session, UserRole.STAFF, "amy@example.com", shop=shop, name="Amy")
    customer = make_customer(session, "Customer", "233240000001")
    make_purchase(session, shop, zed, customer)
    make_purchase(session, shop, amy, customer, product="Oil")

    ids = [e["staff"]["id"] for e in _staff_report(client, token).get_json()["staff"]]
    assert ids == [amy.id, zed.id]


# --- errors ---


def test_staff_invalid_date_and_preset(session, client):
    token = super_admin_token(session, client)
    assert _staff_report(client, token, "?preset=bogus").status_code == 400
    assert _staff_report(
        client, token, "?date_from=2026-10-01&date_to=2026-09-01"
    ).status_code == 400
    assert _staff_report(
        client, token, "?preset=today&date_from=2026-09-01"
    ).status_code == 400


def test_staff_nonexistent_shop(session, client):
    token = super_admin_token(session, client)
    assert _staff_report(client, token, "?shop_id=nonexistent").status_code == 404
