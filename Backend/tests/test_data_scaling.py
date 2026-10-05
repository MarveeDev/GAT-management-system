from datetime import datetime, timedelta, timezone
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


def _base_time():
    return datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


# --- customers endpoint (server-side aggregation) --------------------------


def test_customers_requires_auth(client):
    assert client.get("/api/customers").status_code == 401


def test_customers_aggregates_purchase_count(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    c1 = make_customer(session, "Alice", "233000000001")
    c2 = make_customer(session, "Bob", "233000000002")

    base = _base_time()
    make_purchase(session, shop, staff, c1, product="A", created_at=base)
    make_purchase(session, shop, staff, c1, product="B", created_at=base + timedelta(days=1))
    make_purchase(session, shop, staff, c2, product="C", created_at=base + timedelta(days=2))

    resp = client.get("/api/customers", headers=auth_header(token))
    assert resp.status_code == 200
    customers = resp.get_json()["customers"]
    by_id = {c["customer"]["id"]: c for c in customers}

    assert by_id[c1.id]["purchase_count"] == 2
    assert by_id[c2.id]["purchase_count"] == 1
    assert by_id[c1.id]["customer"]["name"] == "Alice"
    assert by_id[c2.id]["customer"]["phone"] == "233000000002"


def test_customers_last_purchase_and_ordering(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    c1 = make_customer(session, "Alice", "233000000001")
    c2 = make_customer(session, "Bob", "233000000002")

    base = _base_time()
    make_purchase(session, shop, staff, c1, product="A", created_at=base)
    make_purchase(session, shop, staff, c2, product="B", created_at=base + timedelta(days=5))

    resp = client.get("/api/customers", headers=auth_header(token))
    customers = resp.get_json()["customers"]

    # Most recent purchase first.
    assert customers[0]["customer"]["id"] == c2.id
    assert customers[1]["customer"]["id"] == c1.id
    assert customers[0]["last_purchase_at"] is not None
    assert customers[1]["last_purchase_at"] is not None


def test_customers_manager_sees_only_own_shop(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff_a = make_user(session, UserRole.STAFF, "staffa@example.com", shop=shop_a)
    staff_b = make_user(session, UserRole.STAFF, "staffb@example.com", shop=shop_b)
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)

    c_a = make_customer(session, "Alice", "233000000001")
    c_b = make_customer(session, "Bob", "233000000002")
    make_purchase(session, shop_a, staff_a, c_a, product="A")
    make_purchase(session, shop_b, staff_b, c_b, product="B")

    token = get_token(client, "mgr@example.com")
    resp = client.get("/api/customers", headers=auth_header(token))
    ids = [c["customer"]["id"] for c in resp.get_json()["customers"]]
    assert ids == [c_a.id]


def test_customers_staff_sees_only_own_shop(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff_a = make_user(session, UserRole.STAFF, "staffa@example.com", shop=shop_a)
    staff_b = make_user(session, UserRole.STAFF, "staffb@example.com", shop=shop_b)

    c_a = make_customer(session, "Alice", "233000000001")
    c_b = make_customer(session, "Bob", "233000000002")
    make_purchase(session, shop_a, staff_a, c_a, product="A")
    make_purchase(session, shop_b, staff_b, c_b, product="B")

    token = get_token(client, "staffa@example.com")
    resp = client.get("/api/customers", headers=auth_header(token))
    ids = [c["customer"]["id"] for c in resp.get_json()["customers"]]
    assert ids == [c_a.id]


# --- purchase list unique_customers summary --------------------------------


def test_purchase_list_reports_unique_customers(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    c1 = make_customer(session, "Alice", "233000000001")
    c2 = make_customer(session, "Bob", "233000000002")

    make_purchase(session, shop, staff, c1, product="A")
    make_purchase(session, shop, staff, c1, product="B")
    make_purchase(session, shop, staff, c2, product="C")

    resp = client.get("/api/purchases?per_page=1", headers=auth_header(token))
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["summary"]["unique_customers"] == 2
    assert body["pagination"]["total"] == 3


def test_purchase_summary_unique_customers_scoped(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff_a = make_user(session, UserRole.STAFF, "staffa@example.com", shop=shop_a)
    staff_b = make_user(session, UserRole.STAFF, "staffb@example.com", shop=shop_b)
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)

    c_a = make_customer(session, "Alice", "233000000001")
    c_b = make_customer(session, "Bob", "233000000002")
    make_purchase(session, shop_a, staff_a, c_a, product="A")
    make_purchase(session, shop_b, staff_b, c_b, product="B")

    token = get_token(client, "mgr@example.com")
    resp = client.get("/api/purchases?per_page=1", headers=auth_header(token))
    assert resp.get_json()["summary"]["unique_customers"] == 1


# --- SMS purchase_ids filter ----------------------------------------------


def test_sms_purchase_ids_filter(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "Alice", "233000000001")

    p1 = make_purchase(session, shop, staff, customer, product="A")
    p2 = make_purchase(session, shop, staff, customer, product="B")
    p3 = make_purchase(session, shop, staff, customer, product="C")
    make_sms_log(session, shop, p1, customer, status=SMSStatus.SENT)
    make_sms_log(session, shop, p2, customer, status=SMSStatus.FAILED)
    make_sms_log(session, shop, p3, customer, status=SMSStatus.PENDING)

    resp = client.get(
        f"/api/sms?purchase_ids={p1.id},{p2.id}", headers=auth_header(token)
    )
    assert resp.status_code == 200
    logs = resp.get_json()["sms_logs"]
    assert {log["purchase_id"] for log in logs} == {p1.id, p2.id}


def test_sms_purchase_ids_filter_scoped(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff_a = make_user(session, UserRole.STAFF, "staffa@example.com", shop=shop_a)
    staff_b = make_user(session, UserRole.STAFF, "staffb@example.com", shop=shop_b)
    customer = make_customer(session, "Alice", "233000000001")

    p_a = make_purchase(session, shop_a, staff_a, customer, product="A")
    p_b = make_purchase(session, shop_b, staff_b, customer, product="B")
    make_sms_log(session, shop_a, p_a, customer, status=SMSStatus.SENT)
    make_sms_log(session, shop_b, p_b, customer, status=SMSStatus.SENT)

    token = get_token(client, "staffa@example.com")
    # Staff in shop A must not see shop B's SMS log even when requested by id.
    resp = client.get(
        f"/api/sms?purchase_ids={p_a.id},{p_b.id}", headers=auth_header(token)
    )
    assert resp.status_code == 200
    logs = resp.get_json()["sms_logs"]
    assert {log["purchase_id"] for log in logs} == {p_a.id}
