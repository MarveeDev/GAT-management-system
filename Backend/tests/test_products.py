from app.models import Product, ProductStatus, UserRole
from app.services.audit_service import AuditAction
from tests.helpers import (
    auth_header,
    get_token,
    make_product,
    make_shop,
    make_user,
    super_admin_token,
)


def _admin_and_shop(session, client):
    token = super_admin_token(session, client)
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    return token, shop_a, shop_b


def _valid_payload(name="Milo 400g"):
    return {
        "name": name,
        "category": "Food Items",
        "minimum_price": "15.00",
        "maximum_price": "20.00",
    }


# --- create ---


def test_super_admin_can_create_product(session, client):
    token = super_admin_token(session, client)
    resp = client.post(
        "/api/products", headers=auth_header(token), json=_valid_payload()
    )
    assert resp.status_code == 201
    product = resp.get_json()["product"]
    assert product["name"] == "Milo 400g"
    assert product["category"] == "Food Items"
    assert product["minimum_price"] == "15.00"
    assert product["maximum_price"] == "20.00"
    assert product["status"] == ProductStatus.ACTIVE


def test_manager_cannot_create_product(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop)
    token = get_token(client, "mgr@example.com")

    resp = client.post("/api/products", headers=auth_header(token), json=_valid_payload())
    assert resp.status_code == 403


def test_staff_cannot_create_product(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    token = get_token(client, "staff@example.com")

    resp = client.post("/api/products", headers=auth_header(token), json=_valid_payload())
    assert resp.status_code == 403


def test_create_product_requires_name(session, client):
    token = super_admin_token(session, client)
    payload = _valid_payload()
    del payload["name"]
    resp = client.post("/api/products", headers=auth_header(token), json=payload)
    assert resp.status_code == 400


def test_create_product_rejects_negative_price(session, client):
    token = super_admin_token(session, client)
    payload = _valid_payload()
    payload["minimum_price"] = "-1.00"
    resp = client.post("/api/products", headers=auth_header(token), json=payload)
    assert resp.status_code == 400


def test_create_product_rejects_invalid_price_range(session, client):
    token = super_admin_token(session, client)
    payload = _valid_payload()
    payload["minimum_price"] = "25.00"
    payload["maximum_price"] = "20.00"
    resp = client.post("/api/products", headers=auth_header(token), json=payload)
    assert resp.status_code == 400


def test_create_product_rejects_unknown_fields(session, client):
    token = super_admin_token(session, client)
    payload = _valid_payload()
    payload["bogus"] = "value"
    resp = client.post("/api/products", headers=auth_header(token), json=payload)
    assert resp.status_code == 400


def test_duplicate_active_product_name_rejected(session, client):
    token = super_admin_token(session, client)
    resp = client.post("/api/products", headers=auth_header(token), json=_valid_payload())
    assert resp.status_code == 201

    resp = client.post("/api/products", headers=auth_header(token), json=_valid_payload())
    assert resp.status_code == 409


def test_duplicate_active_product_name_case_insensitive(session, client):
    token = super_admin_token(session, client)
    client.post("/api/products", headers=auth_header(token), json=_valid_payload())

    payload = _valid_payload("milo 400g")
    resp = client.post("/api/products", headers=auth_header(token), json=payload)
    assert resp.status_code == 409


def test_create_product_creates_audit_log(session, client):
    token = super_admin_token(session, client)
    client.post("/api/products", headers=auth_header(token), json=_valid_payload())

    from app.models import AuditLog

    logs = AuditLog.query.filter_by(action=AuditAction.PRODUCT_CREATED).all()
    assert len(logs) == 1
    assert logs[0].entity_type == "PRODUCT"


# --- view ---


def test_manager_can_view_products(session, client):
    shop = make_shop(session, "Shop A")
    make_product(session, "Milo 400g")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop)
    token = get_token(client, "mgr@example.com")

    resp = client.get("/api/products", headers=auth_header(token))
    assert resp.status_code == 200
    names = [p["name"] for p in resp.get_json()["products"]]
    assert "Milo 400g" in names


def test_staff_can_view_products(session, client):
    shop = make_shop(session, "Shop A")
    make_product(session, "Milo 400g")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    token = get_token(client, "staff@example.com")

    resp = client.get("/api/products", headers=auth_header(token))
    assert resp.status_code == 200
    names = [p["name"] for p in resp.get_json()["products"]]
    assert "Milo 400g" in names


def test_super_admin_can_view_inactive_products(session, client):
    token = super_admin_token(session, client)
    make_product(session, "Inactive Item", status=ProductStatus.INACTIVE)

    resp = client.get("/api/products", headers=auth_header(token))
    assert resp.status_code == 200
    names = [p["name"] for p in resp.get_json()["products"]]
    assert "Inactive Item" in names


def test_manager_does_not_see_inactive_products(session, client):
    shop = make_shop(session, "Shop A")
    make_product(session, "Active Item")
    make_product(session, "Inactive Item", status=ProductStatus.INACTIVE)
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop)
    token = get_token(client, "mgr@example.com")

    resp = client.get("/api/products", headers=auth_header(token))
    names = [p["name"] for p in resp.get_json()["products"]]
    assert "Active Item" in names
    assert "Inactive Item" not in names


# --- update ---


def test_super_admin_can_update_product(session, client):
    token = super_admin_token(session, client)
    product = make_product(session, "Milo 400g")

    resp = client.patch(
        f"/api/products/{product.id}",
        headers=auth_header(token),
        json={"name": "Milo 500g", "maximum_price": "25.00"},
    )
    assert resp.status_code == 200
    body = resp.get_json()["product"]
    assert body["name"] == "Milo 500g"
    assert body["maximum_price"] == "25.00"


def test_manager_cannot_update_product(session, client):
    shop = make_shop(session, "Shop A")
    product = make_product(session, "Milo 400g")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop)
    token = get_token(client, "mgr@example.com")

    resp = client.patch(
        f"/api/products/{product.id}", headers=auth_header(token), json={"name": "X"}
    )
    assert resp.status_code == 403


def test_staff_cannot_update_product(session, client):
    shop = make_shop(session, "Shop A")
    product = make_product(session, "Milo 400g")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    token = get_token(client, "staff@example.com")

    resp = client.patch(
        f"/api/products/{product.id}", headers=auth_header(token), json={"name": "X"}
    )
    assert resp.status_code == 403


def test_super_admin_can_deactivate_product(session, client):
    token = super_admin_token(session, client)
    product = make_product(session, "Milo 400g")

    resp = client.patch(
        f"/api/products/{product.id}", headers=auth_header(token), json={"status": "INACTIVE"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["product"]["status"] == "INACTIVE"

    from app.models import AuditLog

    assert AuditLog.query.filter_by(action=AuditAction.PRODUCT_DEACTIVATED).count() == 1


def test_update_product_invalid_price_range(session, client):
    token = super_admin_token(session, client)
    product = make_product(session, "Milo 400g")

    resp = client.patch(
        f"/api/products/{product.id}",
        headers=auth_header(token),
        json={"minimum_price": "30.00"},
    )
    assert resp.status_code == 400


def test_update_reactivates_without_duplicate_conflict(session, client):
    token = super_admin_token(session, client)
    product = make_product(session, "Milo 400g", status=ProductStatus.INACTIVE)

    resp = client.patch(
        f"/api/products/{product.id}", headers=auth_header(token), json={"status": "ACTIVE"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["product"]["status"] == "ACTIVE"


def test_get_product_returns_404_for_missing(session, client):
    token = super_admin_token(session, client)
    resp = client.get("/api/products/nonexistent-id", headers=auth_header(token))
    assert resp.status_code == 404


# --- model constraints ---


def test_product_model_negative_min_price_rejected(session):
    import pytest
    from sqlalchemy.exc import IntegrityError

    product = Product(
        name="Bad",
        minimum_price=-1,
        maximum_price=20,
        status=ProductStatus.ACTIVE,
    )
    session.add(product)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_product_model_price_range_rejected(session):
    import pytest
    from sqlalchemy.exc import IntegrityError

    product = Product(
        name="Bad",
        minimum_price=20,
        maximum_price=10,
        status=ProductStatus.ACTIVE,
    )
    session.add(product)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()
