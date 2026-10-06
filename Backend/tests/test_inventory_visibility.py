from app.models import ProductStatus, UserRole
from tests.helpers import (
    auth_header,
    get_token,
    make_inventory,
    make_product,
    make_shop,
    make_user,
    super_admin_token,
)


def test_manager_cannot_view_inactive_product_inventory(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop)
    active = make_product(session, "Active Product")
    inactive = make_product(session, "Inactive Product", status=ProductStatus.INACTIVE)
    make_inventory(session, shop, active, 10)
    make_inventory(session, shop, inactive, 5)

    token = get_token(client, "mgr@example.com")
    resp = client.get("/api/inventory", headers=auth_header(token))
    assert resp.status_code == 200
    product_ids = {row["product_id"] for row in resp.get_json()["inventory"]}
    assert product_ids == {active.id}


def test_staff_cannot_view_inactive_product_inventory(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    active = make_product(session, "Active Product")
    inactive = make_product(session, "Inactive Product", status=ProductStatus.INACTIVE)
    make_inventory(session, shop, active, 10)
    make_inventory(session, shop, inactive, 5)

    token = get_token(client, "staff@example.com")
    resp = client.get("/api/inventory", headers=auth_header(token))
    product_ids = {row["product_id"] for row in resp.get_json()["inventory"]}
    assert product_ids == {active.id}


def test_super_admin_can_view_inactive_product_inventory(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    active = make_product(session, "Active Product")
    inactive = make_product(session, "Inactive Product", status=ProductStatus.INACTIVE)
    make_inventory(session, shop, active, 10)
    make_inventory(session, shop, inactive, 5)

    resp = client.get("/api/inventory", headers=auth_header(token))
    product_ids = {row["product_id"] for row in resp.get_json()["inventory"]}
    assert product_ids == {active.id, inactive.id}


def test_manager_cannot_get_inactive_product_inventory(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop)
    inactive = make_product(session, "Inactive Product", status=ProductStatus.INACTIVE)
    make_inventory(session, shop, inactive, 5)

    token = get_token(client, "mgr@example.com")
    resp = client.get(f"/api/inventory/{inactive.id}", headers=auth_header(token))
    assert resp.status_code == 404


def test_super_admin_can_get_inactive_product_inventory(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    inactive = make_product(session, "Inactive Product", status=ProductStatus.INACTIVE)
    make_inventory(session, shop, inactive, 5)

    resp = client.get(f"/api/inventory/{inactive.id}", headers=auth_header(token))
    assert resp.status_code == 200
    assert len(resp.get_json()["inventory"]) == 1
