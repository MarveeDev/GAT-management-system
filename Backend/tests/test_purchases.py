from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.models import AuditLog, Customer, Purchase, UserRole
from app.services.audit_service import AuditAction
from app.services.customer_service import normalize_phone
from tests.helpers import (
    auth_header,
    get_token,
    make_customer,
    make_purchase,
    make_shop,
    make_user,
    super_admin_token,
)


def post_purchase(client, token, payload):
    return client.post("/api/purchases", headers=auth_header(token), json=payload)


def customer_payload(name="John Doe", phone="0240000000", email=None):
    payload = {"name": name, "phone": phone}
    if email is not None:
        payload["email"] = email
    return payload


# --- phone normalization ---


def test_local_phone_normalized():
    assert normalize_phone("0240000000") == "233240000000"


def test_international_phone_normalized():
    assert normalize_phone("+233240000000") == "233240000000"


def test_international_phone_no_plus_normalized():
    assert normalize_phone("233240000000") == "233240000000"


def test_phone_with_spaces_normalized():
    assert normalize_phone("024 000 0000") == "233240000000"


def test_empty_phone_returns_none():
    assert normalize_phone("") is None
    assert normalize_phone(None) is None


# --- customer workflow ---


def test_new_customer_created_during_purchase(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")

    resp = post_purchase(
        client, token,
        {"shop_id": shop.id, "customer": customer_payload(), "product": "Rice 5kg", "amount": 150.00},
    )
    assert resp.status_code == 201
    body = resp.get_json()["purchase"]
    assert body["customer"]["name"] == "John Doe"
    assert body["customer"]["phone"] == "233240000000"
    assert Customer.query.count() == 1


def test_existing_customer_reused_by_phone(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    existing = make_customer(session, "John Doe", "233240000000")

    resp = post_purchase(
        client, token,
        {"shop_id": shop.id, "customer": customer_payload(phone="+233240000000"), "product": "Rice", "amount": 10},
    )
    assert resp.status_code == 201
    assert resp.get_json()["purchase"]["customer_id"] == existing.id
    assert Customer.query.count() == 1


def test_same_customer_can_purchase_from_multiple_shops(session, client):
    token = super_admin_token(session, client)
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")

    r1 = post_purchase(client, token, {"shop_id": shop_a.id, "customer": customer_payload(), "product": "Rice", "amount": 10})
    r2 = post_purchase(client, token, {"shop_id": shop_b.id, "customer": customer_payload(), "product": "Oil", "amount": 20})

    assert r1.status_code == 201 and r2.status_code == 201
    assert r1.get_json()["purchase"]["customer_id"] == r2.get_json()["purchase"]["customer_id"]
    assert r1.get_json()["purchase"]["shop_id"] != r2.get_json()["purchase"]["shop_id"]
    assert Customer.query.count() == 1


def test_no_duplicate_customer_for_equivalent_phone(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")

    post_purchase(client, token, {"shop_id": shop.id, "customer": customer_payload(phone="0240000000"), "product": "A", "amount": 10})
    post_purchase(client, token, {"shop_id": shop.id, "customer": customer_payload(phone="+233240000000"), "product": "B", "amount": 20})

    assert Customer.query.count() == 1


def test_invalid_customer_data_rejected(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")

    resp = post_purchase(
        client, token,
        {"shop_id": shop.id, "customer": {"phone": "0240000000"}, "product": "Rice", "amount": 10},
    )
    assert resp.status_code == 400


def test_invalid_customer_id_rejected(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")

    resp = post_purchase(
        client, token,
        {"shop_id": shop.id, "customer_id": "nonexistent", "product": "Rice", "amount": 10},
    )
    assert resp.status_code == 404


# --- purchase creation ---


def test_staff_can_create_purchase(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    token = get_token(client, "staff@example.com")

    resp = post_purchase(client, token, {"customer": customer_payload(), "product": "Rice", "amount": 10})
    assert resp.status_code == 201


def test_shop_manager_can_create_purchase(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop)
    token = get_token(client, "mgr@example.com")

    resp = post_purchase(client, token, {"customer": customer_payload(), "product": "Rice", "amount": 10})
    assert resp.status_code == 201


def test_super_admin_can_create_purchase(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")

    resp = post_purchase(client, token, {"shop_id": shop.id, "customer": customer_payload(), "product": "Rice", "amount": 10})
    assert resp.status_code == 201


def test_purchase_stores_correct_shop_id(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    token = get_token(client, "staff@example.com")

    resp = post_purchase(client, token, {"customer": customer_payload(), "product": "Rice", "amount": 10})
    assert resp.get_json()["purchase"]["shop_id"] == shop.id


def test_purchase_stores_authenticated_staff_id(session, client):
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    token = get_token(client, "staff@example.com")

    resp = post_purchase(client, token, {"customer": customer_payload(), "product": "Rice", "amount": 10})
    assert resp.get_json()["purchase"]["staff_id"] == staff.id


def test_purchase_response_includes_staff_identity(session, client):
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    token = get_token(client, "staff@example.com")

    resp = post_purchase(client, token, {"customer": customer_payload(), "product": "Rice", "amount": 10})
    assert resp.status_code == 201
    body = resp.get_json()["purchase"]
    assert body["staff"]["id"] == staff.id
    assert body["staff"]["name"] == "staff"
    assert body["staff"]["email"] == "staff@example.com"
    assert body["staff"]["role"] == "STAFF"
    assert "password" not in body["staff"]


def test_purchase_list_includes_staff_identity(session, client):
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    make_purchase(session, shop, staff, customer, product="Rice")
    token = get_token(client, "staff@example.com")

    resp = client.get("/api/purchases", headers=auth_header(token))
    body = resp.get_json()
    assert body["purchases"][0]["staff"]["name"] == "staff"
    assert body["purchases"][0]["staff"]["email"] == "staff@example.com"
    assert body["purchases"][0]["staff"]["role"] == "STAFF"


def test_product_required(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    token = get_token(client, "staff@example.com")

    resp = post_purchase(client, token, {"customer": customer_payload(), "amount": 10})
    assert resp.status_code == 400


def test_amount_required(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    token = get_token(client, "staff@example.com")

    resp = post_purchase(client, token, {"customer": customer_payload(), "product": "Rice"})
    assert resp.status_code == 400


def test_negative_amount_rejected(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    token = get_token(client, "staff@example.com")

    resp = post_purchase(client, token, {"customer": customer_payload(), "product": "Rice", "amount": -5})
    assert resp.status_code == 400


def test_invalid_amount_rejected(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    token = get_token(client, "staff@example.com")

    resp = post_purchase(client, token, {"customer": customer_payload(), "product": "Rice", "amount": "abc"})
    assert resp.status_code == 400


def test_currency_defaults_to_ghs(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    token = get_token(client, "staff@example.com")

    resp = post_purchase(client, token, {"customer": customer_payload(), "product": "Rice", "amount": 10})
    assert resp.get_json()["purchase"]["currency"] == "GHS"


def test_currency_normalized_to_uppercase(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    token = get_token(client, "staff@example.com")

    resp = post_purchase(client, token, {"customer": customer_payload(), "product": "Rice", "amount": 10, "currency": "ghs"})
    assert resp.get_json()["purchase"]["currency"] == "GHS"


def test_unsupported_currency_rejected(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    token = get_token(client, "staff@example.com")

    resp = post_purchase(client, token, {"customer": customer_payload(), "product": "Rice", "amount": 10, "currency": "USD"})
    assert resp.status_code == 400


def test_inactive_shop_rejects_purchase(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A", status="INACTIVE")

    resp = post_purchase(client, token, {"shop_id": shop.id, "customer": customer_payload(), "product": "Rice", "amount": 10})
    assert resp.status_code == 400


def test_nonexistent_shop_rejected(session, client):
    token = super_admin_token(session, client)
    resp = post_purchase(client, token, {"shop_id": "nonexistent", "customer": customer_payload(), "product": "Rice", "amount": 10})
    assert resp.status_code == 404


def test_staff_cannot_create_purchase_for_another_shop(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop_a)
    token = get_token(client, "staff@example.com")

    resp = post_purchase(client, token, {"shop_id": shop_b.id, "customer": customer_payload(), "product": "Rice", "amount": 10})
    assert resp.status_code == 403


def test_manager_cannot_create_purchase_for_another_shop(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)
    token = get_token(client, "mgr@example.com")

    resp = post_purchase(client, token, {"shop_id": shop_b.id, "customer": customer_payload(), "product": "Rice", "amount": 10})
    assert resp.status_code == 403


def test_client_provided_staff_id_rejected(session, client):
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    make_user(session, UserRole.STAFF, "other@example.com", shop=shop)
    token = get_token(client, "staff@example.com")

    resp = post_purchase(
        client, token,
        {"staff_id": "someone-else", "customer": customer_payload(), "product": "Rice", "amount": 10},
    )
    # staff_id is not an accepted field -> rejected
    assert resp.status_code == 400
    assert Purchase.query.count() == 0


def test_purchase_creates_audit_record_atomically(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    token = get_token(client, "staff@example.com")

    resp = post_purchase(client, token, {"customer": customer_payload(), "product": "Rice", "amount": 10})
    assert resp.status_code == 201
    assert Purchase.query.count() == 1
    assert AuditLog.query.filter_by(action=AuditAction.PURCHASE_CREATED).count() == 1


def test_super_admin_requires_shop_id(session, client):
    token = super_admin_token(session, client)
    resp = post_purchase(client, token, {"customer": customer_payload(), "product": "Rice", "amount": 10})
    assert resp.status_code == 400


def test_failed_purchase_leaves_no_orphan_customer(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    token = get_token(client, "staff@example.com")

    resp = post_purchase(client, token, {"customer": customer_payload(), "product": "Rice", "amount": "abc"})
    assert resp.status_code == 400
    assert Customer.query.count() == 0
    assert Purchase.query.count() == 0


# --- shop isolation ---


def test_staff_cannot_view_another_shops_purchase(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff_b = make_user(session, UserRole.STAFF, "staffb@example.com", shop=shop_b)
    staff_a = make_user(session, UserRole.STAFF, "staffa@example.com", shop=shop_a)
    customer = make_customer(session, "John", "233240000000")
    purchase = make_purchase(session, shop_b, staff_b, customer)

    token = get_token(client, "staffa@example.com")
    resp = client.get(f"/api/purchases/{purchase.id}", headers=auth_header(token))
    assert resp.status_code == 403


def test_manager_cannot_view_another_shops_purchase(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff_b = make_user(session, UserRole.STAFF, "staffb@example.com", shop=shop_b)
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)
    customer = make_customer(session, "John", "233240000000")
    purchase = make_purchase(session, shop_b, staff_b, customer)

    token = get_token(client, "mgr@example.com")
    resp = client.get(f"/api/purchases/{purchase.id}", headers=auth_header(token))
    assert resp.status_code == 403


def test_staff_cannot_list_another_shops_purchases(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff_b = make_user(session, UserRole.STAFF, "staffb@example.com", shop=shop_b)
    make_user(session, UserRole.STAFF, "staffa@example.com", shop=shop_a)
    customer = make_customer(session, "John", "233240000000")
    make_purchase(session, shop_b, staff_b, customer)

    token = get_token(client, "staffa@example.com")
    resp = client.get("/api/purchases", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.get_json()["purchases"] == []


def test_manager_cannot_list_another_shops_purchases(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff_b = make_user(session, UserRole.STAFF, "staffb@example.com", shop=shop_b)
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)
    customer = make_customer(session, "John", "233240000000")
    make_purchase(session, shop_b, staff_b, customer)

    token = get_token(client, "mgr@example.com")
    resp = client.get(f"/api/purchases?shop_id={shop_b.id}", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.get_json()["purchases"] == []


def test_super_admin_can_view_purchases_across_shops(session, client):
    token = super_admin_token(session, client)
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff_a = make_user(session, UserRole.STAFF, "staffa@example.com", shop=shop_a)
    staff_b = make_user(session, UserRole.STAFF, "staffb@example.com", shop=shop_b)
    customer = make_customer(session, "John", "233240000000")
    make_purchase(session, shop_a, staff_a, customer, product="Rice")
    make_purchase(session, shop_b, staff_b, customer, product="Oil")

    resp = client.get("/api/purchases", headers=auth_header(token))
    assert resp.status_code == 200
    assert len(resp.get_json()["purchases"]) == 2


# --- listing & pagination ---


def test_purchase_listing_works(session, client):
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    make_purchase(session, shop, staff, customer, product="Rice")
    token = get_token(client, "staff@example.com")

    resp = client.get("/api/purchases", headers=auth_header(token))
    assert resp.status_code == 200
    body = resp.get_json()
    assert len(body["purchases"]) == 1
    assert body["pagination"]["total"] == 1


def test_pagination_works(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    for i in range(5):
        make_purchase(session, shop, staff, customer, product=f"Item {i}")

    resp = client.get("/api/purchases?page=1&per_page=2", headers=auth_header(token))
    body = resp.get_json()
    assert len(body["purchases"]) == 2
    assert body["pagination"]["page"] == 1
    assert body["pagination"]["per_page"] == 2
    assert body["pagination"]["total"] == 5
    assert body["pagination"]["pages"] == 3


def test_per_page_limit_enforced(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    make_purchase(session, shop, staff, customer)

    resp = client.get("/api/purchases?per_page=999", headers=auth_header(token))
    assert resp.get_json()["pagination"]["per_page"] == 100


def test_shop_id_filter_for_super_admin(session, client):
    token = super_admin_token(session, client)
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff_a = make_user(session, UserRole.STAFF, "staffa@example.com", shop=shop_a)
    staff_b = make_user(session, UserRole.STAFF, "staffb@example.com", shop=shop_b)
    customer = make_customer(session, "John", "233240000000")
    make_purchase(session, shop_a, staff_a, customer, product="Rice")
    make_purchase(session, shop_b, staff_b, customer, product="Oil")

    resp = client.get(f"/api/purchases?shop_id={shop_a.id}", headers=auth_header(token))
    purchases = resp.get_json()["purchases"]
    assert len(purchases) == 1
    assert purchases[0]["product"] == "Rice"


def test_shop_id_filter_cannot_escape_scope(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff_a = make_user(session, UserRole.STAFF, "staffa@example.com", shop=shop_a)
    staff_b = make_user(session, UserRole.STAFF, "staffb@example.com", shop=shop_b)
    customer = make_customer(session, "John", "233240000000")
    make_purchase(session, shop_a, staff_a, customer, product="Rice")
    make_purchase(session, shop_b, staff_b, customer, product="Oil")
    token = get_token(client, "staffa@example.com")

    resp = client.get(f"/api/purchases?shop_id={shop_b.id}", headers=auth_header(token))
    purchases = resp.get_json()["purchases"]
    assert len(purchases) == 1
    assert purchases[0]["product"] == "Rice"


def test_staff_id_filter_respects_shop_scope(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff_a = make_user(session, UserRole.STAFF, "staffa@example.com", shop=shop_a)
    staff_b = make_user(session, UserRole.STAFF, "staffb@example.com", shop=shop_b)
    customer = make_customer(session, "John", "233240000000")
    make_purchase(session, shop_a, staff_a, customer, product="Rice")
    make_purchase(session, shop_b, staff_b, customer, product="Oil")
    token = get_token(client, "staffa@example.com")

    # filtering by another shop's staff id yields nothing
    resp = client.get(f"/api/purchases?staff_id={staff_b.id}", headers=auth_header(token))
    assert resp.get_json()["purchases"] == []


def test_customer_id_filter_respects_shop_scope(session, client):
    shop_a = make_shop(session, "Shop A")
    staff_a = make_user(session, UserRole.STAFF, "staffa@example.com", shop=shop_a)
    customer = make_customer(session, "John", "233240000000")
    make_purchase(session, shop_a, staff_a, customer, product="Rice")
    token = get_token(client, "staffa@example.com")

    resp = client.get(f"/api/purchases?customer_id={customer.id}", headers=auth_header(token))
    assert len(resp.get_json()["purchases"]) == 1


def test_date_from_filter(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    base = datetime(2024, 6, 1, 12, 0, 0)
    make_purchase(session, shop, staff, customer, product="Old", created_at=base - timedelta(days=100))
    make_purchase(session, shop, staff, customer, product="New", created_at=base)

    resp = client.get("/api/purchases?date_from=2024-05-01", headers=auth_header(token))
    products = [p["product"] for p in resp.get_json()["purchases"]]
    assert "New" in products and "Old" not in products


def test_date_to_filter(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    base = datetime(2024, 6, 1, 12, 0, 0)
    make_purchase(session, shop, staff, customer, product="Old", created_at=base - timedelta(days=100))
    make_purchase(session, shop, staff, customer, product="New", created_at=base)

    resp = client.get("/api/purchases?date_to=2024-05-01", headers=auth_header(token))
    products = [p["product"] for p in resp.get_json()["purchases"]]
    assert "Old" in products and "New" not in products


def test_search_filter(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    make_purchase(session, shop, staff, customer, product="Samsung A25")
    make_purchase(session, shop, staff, customer, product="Rice")

    resp = client.get("/api/purchases?search=Samsung", headers=auth_header(token))
    products = [p["product"] for p in resp.get_json()["purchases"]]
    assert products == ["Samsung A25"]


# --- detail ---


def test_existing_purchase_retrieved(session, client):
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    customer = make_customer(session, "John", "233240000000")
    purchase = make_purchase(session, shop, staff, customer, product="Rice")
    token = get_token(client, "staff@example.com")

    resp = client.get(f"/api/purchases/{purchase.id}", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.get_json()["purchase"]["product"] == "Rice"


def test_missing_purchase_returns_404(session, client):
    token = super_admin_token(session, client)
    resp = client.get("/api/purchases/nonexistent", headers=auth_header(token))
    assert resp.status_code == 404


def test_cross_shop_purchase_access_returns_403(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff_b = make_user(session, UserRole.STAFF, "staffb@example.com", shop=shop_b)
    make_user(session, UserRole.STAFF, "staffa@example.com", shop=shop_a)
    customer = make_customer(session, "John", "233240000000")
    purchase = make_purchase(session, shop_b, staff_b, customer)
    token = get_token(client, "staffa@example.com")

    resp = client.get(f"/api/purchases/{purchase.id}", headers=auth_header(token))
    assert resp.status_code == 403


# --- audit ---


def test_purchase_creation_creates_audit_log(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    post_purchase(client, token, {"shop_id": shop.id, "customer": customer_payload(), "product": "Rice", "amount": 10})

    logs = AuditLog.query.filter_by(action=AuditAction.PURCHASE_CREATED).all()
    assert len(logs) == 1


def test_audit_record_contains_authenticated_user_and_shop_and_purchase(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    admin = make_user(session, UserRole.SUPER_ADMIN, "admin2@example.com")
    token2 = get_token(client, "admin2@example.com")

    resp = post_purchase(client, token2, {"shop_id": shop.id, "customer": customer_payload(), "product": "Rice", "amount": 10})
    purchase_id = resp.get_json()["purchase"]["id"]

    log = AuditLog.query.filter_by(action=AuditAction.PURCHASE_CREATED).first()
    assert log.user_id == admin.id
    assert log.shop_id == shop.id
    assert log.entity_id == purchase_id
    assert log.entity_type == "PURCHASE"


def test_audit_description_contains_no_secrets(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    post_purchase(client, token, {"shop_id": shop.id, "customer": customer_payload(), "product": "Rice", "amount": 10})

    for log in AuditLog.query.all():
        text = (log.description or "") + (log.action or "")
        assert "password" not in text.lower()
        assert "jwt" not in text.lower()
        assert "eyJ" not in text


# --- security ---


def test_missing_jwt_rejected(client):
    assert client.post("/api/purchases", json={}).status_code == 401
    assert client.get("/api/purchases").status_code == 401


def test_invalid_jwt_rejected(client):
    assert client.get("/api/purchases", headers=auth_header("bad-token")).status_code == 401


def test_inactive_user_rejected(session, client):
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    token = get_token(client, "staff@example.com")
    staff.status = "INACTIVE"
    session.commit()

    resp = post_purchase(client, token, {"customer": customer_payload(), "product": "Rice", "amount": 10})
    assert resp.status_code == 401
