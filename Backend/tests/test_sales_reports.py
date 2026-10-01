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


def _sales(client, token, query=""):
    return client.get(f"/api/reports/sales{query}", headers=auth_header(token))


def _shop_staff_customer(session, shop_name, staff_email, phone):
    shop = make_shop(session, shop_name)
    staff = make_user(session, UserRole.STAFF, staff_email, shop=shop)
    customer = make_customer(session, "Customer", phone)
    return shop, staff, customer


# --- authentication ---


def test_sales_requires_auth(client):
    assert client.get("/api/reports/sales").status_code == 401


# --- super admin scope ---


def test_super_admin_sales_across_shops(session, client):
    token = super_admin_token(session, client)
    shop_a, staff_a, customer_a = _shop_staff_customer(
        session, "Shop A", "staffa@example.com", "233240000001"
    )
    shop_b, staff_b, customer_b = _shop_staff_customer(
        session, "Shop B", "staffb@example.com", "233240000002"
    )
    make_purchase(session, shop_a, staff_a, customer_a, amount=Decimal("100.00"))
    make_purchase(session, shop_b, staff_b, customer_b, amount=Decimal("200.00"))

    resp = _sales(client, token)
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["sales"]) == 2
    assert data["summary"]["total_purchases"] == 2
    assert data["summary"]["total_sales"] == "300.00"


def test_super_admin_sales_shop_filter(session, client):
    token = super_admin_token(session, client)
    shop_a, staff_a, customer_a = _shop_staff_customer(
        session, "Shop A", "staffa@example.com", "233240000001"
    )
    shop_b, staff_b, customer_b = _shop_staff_customer(
        session, "Shop B", "staffb@example.com", "233240000002"
    )
    make_purchase(session, shop_a, staff_a, customer_a, amount=Decimal("100.00"))
    make_purchase(session, shop_b, staff_b, customer_b, amount=Decimal("200.00"))

    resp = _sales(client, token, f"?shop_id={shop_a.id}")
    data = resp.get_json()
    assert len(data["sales"]) == 1
    assert data["sales"][0]["shop"]["id"] == shop_a.id
    assert data["summary"]["total_sales"] == "100.00"


# --- manager scope ---


def test_manager_sales_own_shop(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)
    staff_a = make_user(session, UserRole.STAFF, "staffa@example.com", shop=shop_a)
    staff_b = make_user(session, UserRole.STAFF, "staffb@example.com", shop=shop_b)
    customer = make_customer(session, "Customer", "233240000001")
    make_purchase(session, shop_a, staff_a, customer, amount=Decimal("100.00"))
    make_purchase(session, shop_b, staff_b, customer, amount=Decimal("200.00"))

    token = get_token(client, "mgr@example.com")
    data = _sales(client, token).get_json()
    assert len(data["sales"]) == 1
    assert data["sales"][0]["shop"]["id"] == shop_a.id


def test_manager_sales_cross_shop_denied(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)
    token = get_token(client, "mgr@example.com")

    assert _sales(client, token, f"?shop_id={shop_b.id}").status_code == 403


def test_staff_sales_cross_shop_denied(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop_a)
    token = get_token(client, "staff@example.com")

    assert _sales(client, token).status_code == 200  # own shop
    assert _sales(client, token, f"?shop_id={shop_b.id}").status_code == 403


# --- date range ---


def test_sales_date_filter(session, client):
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

    data = _sales(client, token, "?date_from=2026-09-05&date_to=2026-09-20").get_json()
    assert data["summary"]["total_purchases"] == 1
    assert data["summary"]["total_sales"] == "200.00"
    assert data["sales"][0]["product"] == "Oil"


# --- pagination ---


def test_sales_pagination(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Customer", "233240000001")
    for i in range(5):
        make_purchase(session, shop, staff, customer, product=f"Item {i}")

    page1 = _sales(client, token, "?page=1&per_page=2").get_json()
    assert len(page1["sales"]) == 2
    assert page1["pagination"]["total"] == 5
    assert page1["pagination"]["pages"] == 3
    assert page1["pagination"]["page"] == 1

    page2 = _sales(client, token, "?page=2&per_page=2").get_json()
    assert len(page2["sales"]) == 2

    page3 = _sales(client, token, "?page=3&per_page=2").get_json()
    assert len(page3["sales"]) == 1

    ids = {s["id"] for s in page1["sales"] + page2["sales"] + page3["sales"]}
    assert len(ids) == 5


def test_sales_summary_not_page_limited(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Customer", "233240000001")
    for _ in range(5):
        make_purchase(session, shop, staff, customer, amount=Decimal("100.00"))

    data = _sales(client, token, "?per_page=2").get_json()
    assert len(data["sales"]) == 2
    assert data["summary"]["total_purchases"] == 5
    assert data["summary"]["total_sales"] == "500.00"


# --- record information ---


def test_sales_recorded_by(session, client):
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Customer", "233240000001")
    make_purchase(session, shop, staff, customer)
    token = get_token(client, "staff@example.com")

    row = _sales(client, token).get_json()["sales"][0]
    assert row["recorded_by"]["id"] == staff.id
    assert row["recorded_by"]["name"] == "staff"
    assert row["recorded_by"]["email"] == "staff@example.com"
    assert row["recorded_by"]["role"] == "STAFF"


def test_sales_customer_data(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John Doe", "233240000001")
    make_purchase(session, shop, staff, customer)

    row = _sales(client, token).get_json()["sales"][0]
    assert row["customer"]["id"] == customer.id
    assert row["customer"]["name"] == "John Doe"
    assert row["customer"]["phone"] == "233240000001"


def test_sales_shop_data(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Customer", "233240000001")
    make_purchase(session, shop, staff, customer)

    row = _sales(client, token).get_json()["sales"][0]
    assert row["shop"]["id"] == shop.id
    assert row["shop"]["name"] == "Shop A"


def test_sales_no_secrets(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Customer", "233240000001")
    make_purchase(session, shop, staff, customer)

    text = json.dumps(_sales(client, token).get_json())
    assert "password" not in text
    assert "token" not in text
    assert "secret" not in text


# --- money ---


def test_sales_money_aggregation(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Customer", "233240000001")
    make_purchase(session, shop, staff, customer, amount=Decimal("100.00"))
    make_purchase(session, shop, staff, customer, product="Oil", amount=Decimal("250.00"))
    make_purchase(session, shop, staff, customer, product="Sugar", amount=Decimal("150.00"))

    summary = _sales(client, token).get_json()["summary"]
    assert summary["total_sales"] == "500.00"
    assert summary["average_purchase_value"] == "166.67"


# --- ordering ---


def test_sales_newest_first(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Customer", "233240000001")
    base = datetime(2026, 9, 1, 12, 0, 0)
    make_purchase(session, shop, staff, customer, product="Old", created_at=base)
    make_purchase(
        session, shop, staff, customer, product="New", created_at=base + timedelta(days=5)
    )

    rows = _sales(client, token, "?date_from=2026-09-01&date_to=2026-09-30").get_json()[
        "sales"
    ]
    assert rows[0]["product"] == "New"
    assert rows[1]["product"] == "Old"


# --- invalid pagination ---


def test_sales_invalid_pagination(session, client):
    token = super_admin_token(session, client)
    assert _sales(client, token, "?page=0").status_code == 400
    assert _sales(client, token, "?per_page=0").status_code == 400
    assert _sales(client, token, "?per_page=101").status_code == 400
    assert _sales(client, token, "?page=abc").status_code == 400
    assert _sales(client, token, "?per_page=xyz").status_code == 400
