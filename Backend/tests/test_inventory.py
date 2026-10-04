import pytest
from sqlalchemy.exc import IntegrityError

from app.models import (
    Product,
    ShopInventory,
    StockMovement,
    StockMovementType,
    User,
    UserRole,
)
from app.services.audit_service import AuditAction
from tests.helpers import (
    auth_header,
    get_token,
    make_inventory,
    make_product,
    make_shop,
    make_user,
    super_admin_token,
)


def _setup(session, client):
    admin_token = super_admin_token(session, client)
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    product = make_product(session, "Milo 400g")
    return admin_token, shop_a, shop_b, product


def _manager(session, client, shop):
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop)
    return get_token(client, "mgr@example.com")


def _staff(session, client, shop):
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    return get_token(client, "staff@example.com")


# --- listing ---


def test_super_admin_can_view_all_shop_inventory(session, client):
    token, shop_a, shop_b, product = _setup(session, client)
    make_inventory(session, shop_a, product, 50)
    make_inventory(session, shop_b, product, 30)

    resp = client.get("/api/inventory", headers=auth_header(token))
    assert resp.status_code == 200
    rows = resp.get_json()["inventory"]
    assert len(rows) == 2
    by_shop = {r["shop_id"]: r["quantity"] for r in rows}
    assert by_shop[shop_a.id] == 50
    assert by_shop[shop_b.id] == 30


def test_super_admin_can_view_selected_shop_inventory(session, client):
    token, shop_a, shop_b, product = _setup(session, client)
    make_inventory(session, shop_a, product, 50)
    make_inventory(session, shop_b, product, 30)

    resp = client.get(f"/api/inventory?shop_id={shop_a.id}", headers=auth_header(token))
    assert resp.status_code == 200
    rows = resp.get_json()["inventory"]
    assert len(rows) == 1
    assert rows[0]["shop_id"] == shop_a.id
    assert rows[0]["quantity"] == 50


def test_manager_can_view_only_assigned_shop_inventory(session, client):
    token, shop_a, shop_b, product = _setup(session, client)
    make_inventory(session, shop_a, product, 50)
    make_inventory(session, shop_b, product, 30)

    mgr_token = _manager(session, client, shop_a)
    resp = client.get("/api/inventory", headers=auth_header(mgr_token))
    assert resp.status_code == 200
    rows = resp.get_json()["inventory"]
    assert len(rows) == 1
    assert rows[0]["shop_id"] == shop_a.id


def test_staff_can_view_only_assigned_shop_inventory(session, client):
    token, shop_a, shop_b, product = _setup(session, client)
    make_inventory(session, shop_a, product, 50)
    make_inventory(session, shop_b, product, 30)

    staff_token = _staff(session, client, shop_a)
    resp = client.get("/api/inventory", headers=auth_header(staff_token))
    assert resp.status_code == 200
    rows = resp.get_json()["inventory"]
    assert len(rows) == 1
    assert rows[0]["shop_id"] == shop_a.id


def test_manager_cannot_access_another_shops_inventory(session, client):
    token, shop_a, shop_b, product = _setup(session, client)
    make_inventory(session, shop_a, product, 50)
    make_inventory(session, shop_b, product, 30)

    mgr_token = _manager(session, client, shop_a)
    resp = client.get(f"/api/inventory?shop_id={shop_b.id}", headers=auth_header(mgr_token))
    assert resp.status_code == 403


def test_staff_cannot_access_another_shops_inventory(session, client):
    token, shop_a, shop_b, product = _setup(session, client)
    make_inventory(session, shop_a, product, 50)
    make_inventory(session, shop_b, product, 30)

    staff_token = _staff(session, client, shop_a)
    resp = client.get(f"/api/inventory?shop_id={shop_b.id}", headers=auth_header(staff_token))
    assert resp.status_code == 403


def test_manager_cannot_modify_stock(session, client):
    token, shop_a, shop_b, product = _setup(session, client)
    mgr_token = _manager(session, client, shop_a)

    resp = client.post(
        "/api/inventory",
        headers=auth_header(mgr_token),
        json={"product_id": product.id, "shop_id": shop_a.id, "quantity": 10},
    )
    assert resp.status_code == 403


def test_staff_cannot_modify_stock(session, client):
    token, shop_a, shop_b, product = _setup(session, client)
    staff_token = _staff(session, client, shop_a)

    resp = client.post(
        "/api/inventory",
        headers=auth_header(staff_token),
        json={"product_id": product.id, "shop_id": shop_a.id, "quantity": 10},
    )
    assert resp.status_code == 403


# --- per-product inventory ---


def test_super_admin_views_product_inventory_all_shops(session, client):
    token, shop_a, shop_b, product = _setup(session, client)
    make_inventory(session, shop_a, product, 50)
    make_inventory(session, shop_b, product, 30)

    resp = client.get(f"/api/inventory/{product.id}", headers=auth_header(token))
    assert resp.status_code == 200
    rows = resp.get_json()["inventory"]
    assert len(rows) == 2


def test_manager_views_product_inventory_own_shop_only(session, client):
    token, shop_a, shop_b, product = _setup(session, client)
    make_inventory(session, shop_a, product, 50)
    make_inventory(session, shop_b, product, 30)

    mgr_token = _manager(session, client, shop_a)
    resp = client.get(f"/api/inventory/{product.id}", headers=auth_header(mgr_token))
    assert resp.status_code == 200
    rows = resp.get_json()["inventory"]
    assert len(rows) == 1
    assert rows[0]["shop_id"] == shop_a.id


# --- stock setting / movement history ---


def test_initial_stock_creates_movement_history(session, client):
    token, shop_a, shop_b, product = _setup(session, client)

    resp = client.post(
        "/api/inventory",
        headers=auth_header(token),
        json={"product_id": product.id, "shop_id": shop_a.id, "quantity": 50},
    )
    assert resp.status_code == 200
    assert resp.get_json()["inventory"]["quantity"] == 50

    movement = StockMovement.query.filter_by(
        product_id=product.id, shop_id=shop_a.id
    ).first()
    assert movement is not None
    assert movement.movement_type == StockMovementType.INITIAL_STOCK
    assert movement.quantity_before == 0
    assert movement.quantity_after == 50
    assert movement.quantity_change == 50


def test_manual_adjustment_creates_movement_history(session, client):
    token, shop_a, shop_b, product = _setup(session, client)
    make_inventory(session, shop_a, product, 50)

    resp = client.post(
        "/api/inventory",
        headers=auth_header(token),
        json={"product_id": product.id, "shop_id": shop_a.id, "quantity": 30},
    )
    assert resp.status_code == 200

    movement = StockMovement.query.filter_by(
        product_id=product.id,
        shop_id=shop_a.id,
        movement_type=StockMovementType.MANUAL_ADJUSTMENT,
    ).first()
    assert movement is not None
    assert movement.quantity_before == 50
    assert movement.quantity_after == 30
    assert movement.quantity_change == -20


def test_actor_recorded_on_movement(session, client):
    token, shop_a, shop_b, product = _setup(session, client)

    client.post(
        "/api/inventory",
        headers=auth_header(token),
        json={"product_id": product.id, "shop_id": shop_a.id, "quantity": 50},
    )

    admin = User.query.filter_by(email="admin@example.com").first()
    movement = StockMovement.query.filter_by(
        product_id=product.id, shop_id=shop_a.id
    ).first()
    assert movement.actor_id == admin.id


def test_negative_quantity_rejected(session, client):
    token, shop_a, shop_b, product = _setup(session, client)

    resp = client.post(
        "/api/inventory",
        headers=auth_header(token),
        json={"product_id": product.id, "shop_id": shop_a.id, "quantity": -5},
    )
    assert resp.status_code == 400


def test_inventory_independent_per_shop(session, client):
    token, shop_a, shop_b, product = _setup(session, client)
    make_inventory(session, shop_a, product, 50)
    make_inventory(session, shop_b, product, 20)

    # Adjust shop A only.
    client.post(
        "/api/inventory",
        headers=auth_header(token),
        json={"product_id": product.id, "shop_id": shop_a.id, "quantity": 10},
    )

    inv_a = ShopInventory.query.filter_by(
        product_id=product.id, shop_id=shop_a.id
    ).first()
    inv_b = ShopInventory.query.filter_by(
        product_id=product.id, shop_id=shop_b.id
    ).first()
    assert inv_a.quantity == 10
    assert inv_b.quantity == 20


def test_movement_history_endpoint_super_admin_only(session, client):
    token, shop_a, shop_b, product = _setup(session, client)
    make_inventory(session, shop_a, product, 50)

    resp = client.get(f"/api/inventory/{product.id}/movements", headers=auth_header(token))
    assert resp.status_code == 200
    assert len(resp.get_json()["movements"]) >= 0

    mgr_token = _manager(session, client, shop_a)
    resp = client.get(f"/api/inventory/{product.id}/movements", headers=auth_header(mgr_token))
    assert resp.status_code == 403


def test_initial_stock_creates_audit_log(session, client):
    from app.models import AuditLog

    token, shop_a, shop_b, product = _setup(session, client)
    client.post(
        "/api/inventory",
        headers=auth_header(token),
        json={"product_id": product.id, "shop_id": shop_a.id, "quantity": 50},
    )
    assert AuditLog.query.filter_by(action=AuditAction.STOCK_INITIALIZED).count() == 1


def test_stock_adjustment_creates_audit_log(session, client):
    from app.models import AuditLog

    token, shop_a, shop_b, product = _setup(session, client)
    make_inventory(session, shop_a, product, 50)
    client.post(
        "/api/inventory",
        headers=auth_header(token),
        json={"product_id": product.id, "shop_id": shop_a.id, "quantity": 30},
    )
    assert AuditLog.query.filter_by(action=AuditAction.STOCK_ADJUSTED).count() == 1


# --- model constraints ---


def test_duplicate_product_shop_inventory_prevented(session):
    shop = make_shop(session, "Shop A")
    product = make_product(session, "Milo 400g")
    make_inventory(session, shop, product, 10)

    duplicate = ShopInventory(shop_id=shop.id, product_id=product.id, quantity=20)
    session.add(duplicate)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_negative_inventory_quantity_rejected(session):
    shop = make_shop(session, "Shop A")
    product = make_product(session, "Milo 400g")

    inventory = ShopInventory(shop_id=shop.id, product_id=product.id, quantity=-1)
    session.add(inventory)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_inventory_relationship_to_product_and_shop(session):
    shop = make_shop(session, "Shop A")
    product = make_product(session, "Milo 400g")
    inventory = make_inventory(session, shop, product, 25)

    loaded = ShopInventory.query.first()
    assert loaded.product.id == product.id
    assert loaded.shop.id == shop.id
    assert loaded.quantity == 25
