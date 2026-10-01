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


def _customers_report(client, token, query=""):
    return client.get(f"/api/reports/customers{query}", headers=auth_header(token))


def _customer_by_id(data, customer_id):
    for entry in data["customers"]:
        if entry["customer"]["id"] == customer_id:
            return entry
    return None


# --- authentication ---


def test_customers_requires_auth(client):
    assert client.get("/api/reports/customers").status_code == 401


# --- scope / authorization ---


def test_super_admin_all_customers(session, client):
    token = super_admin_token(session, client)
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop_a)
    customer_a = make_customer(session, "A", "233240000001")
    customer_b = make_customer(session, "B", "233240000002")
    make_purchase(session, shop_a, staff, customer_a)
    make_purchase(session, shop_b, staff, customer_b)

    data = _customers_report(client, token).get_json()
    ids = {entry["customer"]["id"] for entry in data["customers"]}
    assert ids == {customer_a.id, customer_b.id}


def test_super_admin_customer_shop_filter(session, client):
    token = super_admin_token(session, client)
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop_a)
    customer_a = make_customer(session, "A", "233240000001")
    customer_b = make_customer(session, "B", "233240000002")
    make_purchase(session, shop_a, staff, customer_a)
    make_purchase(session, shop_b, staff, customer_b)

    data = _customers_report(client, token, f"?shop_id={shop_a.id}").get_json()
    ids = [entry["customer"]["id"] for entry in data["customers"]]
    assert ids == [customer_a.id]


def test_manager_own_shop(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop_a)
    customer_a = make_customer(session, "A", "233240000001")
    customer_b = make_customer(session, "B", "233240000002")
    make_purchase(session, shop_a, staff, customer_a)
    make_purchase(session, shop_b, staff, customer_b)

    token = get_token(client, "mgr@example.com")
    data = _customers_report(client, token).get_json()
    ids = [entry["customer"]["id"] for entry in data["customers"]]
    assert ids == [customer_a.id]


def test_manager_cross_shop_denied(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)
    token = get_token(client, "mgr@example.com")

    assert _customers_report(client, token, f"?shop_id={shop_b.id}").status_code == 403


def test_staff_cross_shop_denied(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop_a)
    token = get_token(client, "staff@example.com")

    assert _customers_report(client, token).status_code == 200  # own shop
    assert _customers_report(client, token, f"?shop_id={shop_b.id}").status_code == 403


# --- metrics ---


def test_customer_identity_from_customer_id(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Kofi Mensah", "0241234567")
    make_purchase(session, shop, staff, customer)

    entry = _customers_report(client, token).get_json()["customers"][0]
    assert entry["customer"]["id"] == customer.id
    assert entry["customer"]["name"] == "Kofi Mensah"
    assert entry["customer"]["phone"] == "0241234567"


def test_customer_grouped_metrics(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Customer", "233240000001")
    make_purchase(session, shop, staff, customer, amount=Decimal("100.00"))
    make_purchase(session, shop, staff, customer, product="Oil", amount=Decimal("250.00"))
    make_purchase(session, shop, staff, customer, product="Sugar", amount=Decimal("150.00"))

    entry = _customers_report(client, token).get_json()["customers"][0]
    assert entry["metrics"]["total_purchases"] == 3
    assert entry["metrics"]["total_spent"] == "500.00"
    assert entry["metrics"]["average_purchase_value"] == "166.67"


def test_customers_grouped_independently(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer_a = make_customer(session, "A", "233240000001")
    customer_b = make_customer(session, "B", "233240000002")
    make_purchase(session, shop, staff, customer_a)
    make_purchase(session, shop, staff, customer_b)
    make_purchase(session, shop, staff, customer_b, product="Oil")

    data = _customers_report(client, token).get_json()
    assert len(data["customers"]) == 2
    a = _customer_by_id(data, customer_a.id)
    b = _customer_by_id(data, customer_b.id)
    assert a["metrics"]["total_purchases"] == 1
    assert b["metrics"]["total_purchases"] == 2


# --- multi-shop customer handling ---


def test_multi_shop_customer_aggregated_once(session, client):
    token = super_admin_token(session, client)
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff_a = make_user(session, UserRole.STAFF, "staffa@example.com", shop=shop_a)
    staff_b = make_user(session, UserRole.STAFF, "staffb@example.com", shop=shop_b)
    customer = make_customer(session, "Shared", "233240000001")
    make_purchase(session, shop_a, staff_a, customer, amount=Decimal("100.00"))
    make_purchase(session, shop_b, staff_b, customer, amount=Decimal("200.00"))

    data = _customers_report(client, token).get_json()
    assert len(data["customers"]) == 1
    entry = data["customers"][0]
    assert entry["metrics"]["total_purchases"] == 2
    assert entry["metrics"]["total_spent"] == "300.00"
    assert {s["id"] for s in entry["shops"]} == {shop_a.id, shop_b.id}

    totals = data["totals"]
    assert totals["total_customers"] == 1
    assert totals["total_purchases"] == 2
    assert totals["total_spent"] == "300.00"


def test_multi_shop_customer_shop_filter_limits(session, client):
    token = super_admin_token(session, client)
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff_a = make_user(session, UserRole.STAFF, "staffa@example.com", shop=shop_a)
    staff_b = make_user(session, UserRole.STAFF, "staffb@example.com", shop=shop_b)
    customer = make_customer(session, "Shared", "233240000001")
    make_purchase(session, shop_a, staff_a, customer, amount=Decimal("100.00"))
    make_purchase(session, shop_b, staff_b, customer, amount=Decimal("200.00"))

    data = _customers_report(client, token, f"?shop_id={shop_a.id}").get_json()
    entry = data["customers"][0]
    assert entry["metrics"]["total_purchases"] == 1
    assert entry["metrics"]["total_spent"] == "100.00"
    assert [s["id"] for s in entry["shops"]] == [shop_a.id]


def test_customer_shop_information(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Customer", "233240000001")
    make_purchase(session, shop, staff, customer)

    entry = _customers_report(client, token).get_json()["customers"][0]
    assert entry["shops"][0]["id"] == shop.id
    assert entry["shops"][0]["name"] == "Shop A"
    assert entry["shops"][0]["status"] == "ACTIVE"


def test_customers_no_secrets(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Customer", "233240000001")
    make_purchase(session, shop, staff, customer)

    text = json.dumps(_customers_report(client, token).get_json())
    assert "password" not in text
    assert "token" not in text
    assert "secret" not in text
    assert "api_key" not in text


# --- date range ---


def test_customer_date_filter(session, client):
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

    data = _customers_report(
        client, token, "?date_from=2026-09-05&date_to=2026-09-20"
    ).get_json()
    entry = data["customers"][0]
    assert entry["metrics"]["total_purchases"] == 1
    assert entry["metrics"]["total_spent"] == "200.00"


# --- empty / ordering ---


def test_customers_empty_range(session, client):
    token = super_admin_token(session, client)
    data = _customers_report(client, token).get_json()
    assert data["customers"] == []
    assert data["totals"]["total_customers"] == 0
    assert data["totals"]["total_purchases"] == 0
    assert data["totals"]["total_spent"] == "0.00"


def test_customers_ordering(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer_low = make_customer(session, "Low", "233240000001")
    customer_high = make_customer(session, "High", "233240000002")
    make_purchase(session, shop, staff, customer_low)
    make_purchase(session, shop, staff, customer_high)
    make_purchase(session, shop, staff, customer_high, product="Oil")
    make_purchase(session, shop, staff, customer_high, product="Sugar")

    ids = [
        entry["customer"]["id"]
        for entry in _customers_report(client, token).get_json()["customers"]
    ]
    assert ids == [customer_high.id, customer_low.id]


def test_customers_ordering_name_tiebreak(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer_zed = make_customer(session, "Zed", "233240000001")
    customer_amy = make_customer(session, "Amy", "233240000002")
    make_purchase(session, shop, staff, customer_zed)
    make_purchase(session, shop, staff, customer_amy, product="Oil")

    ids = [
        entry["customer"]["id"]
        for entry in _customers_report(client, token).get_json()["customers"]
    ]
    assert ids == [customer_amy.id, customer_zed.id]


# --- errors ---


def test_customers_invalid_date_and_preset(session, client):
    token = super_admin_token(session, client)
    assert _customers_report(client, token, "?preset=bogus").status_code == 400
    assert _customers_report(
        client, token, "?date_from=2026-10-01&date_to=2026-09-01"
    ).status_code == 400
    assert _customers_report(
        client, token, "?preset=today&date_from=2026-09-01"
    ).status_code == 400


def test_customers_nonexistent_shop(session, client):
    token = super_admin_token(session, client)
    assert _customers_report(client, token, "?shop_id=nonexistent").status_code == 404
