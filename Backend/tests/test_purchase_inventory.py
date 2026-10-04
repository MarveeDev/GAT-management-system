from decimal import Decimal

import pytest

from app.models import (
    AuditLog,
    Product,
    Purchase,
    ShopInventory,
    SMSLog,
    SMSStatus,
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
    make_template,
    make_user,
    super_admin_token,
)


def _customer():
    return {"name": "John Doe", "phone": "0240000000"}


def _inventory_payload(product_id, quantity, unit_price, shop_id=None):
    payload = {
        "product_id": product_id,
        "quantity": quantity,
        "unit_price": unit_price,
        "customer": _customer(),
    }
    if shop_id:
        payload["shop_id"] = shop_id
    return payload


def _post(client, token, payload):
    return client.post("/api/purchases", headers=auth_header(token), json=payload)


def _setup_product_with_stock(session, client, stock=50, min_price="15.00", max_price="20.00"):
    admin_token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    product = make_product(
        session, "Milo 400g",
        minimum_price=Decimal(min_price),
        maximum_price=Decimal(max_price),
    )
    make_inventory(session, shop, product, stock)
    return admin_token, shop, product


# --- product / purchase link ---


def test_super_admin_can_make_inventory_purchase(session, client):
    token, shop, product = _setup_product_with_stock(session, client)
    resp = _post(client, token, _inventory_payload(product.id, 3, "18.00", shop.id))
    assert resp.status_code == 201
    body = resp.get_json()["purchase"]
    assert body["product_id"] == product.id
    assert body["product"] == "Milo 400g"
    assert body["quantity"] == 3
    assert body["unit_price"] == "18.00"
    assert body["amount"] == "54.00"


def test_manager_can_make_inventory_purchase(session, client):
    shop = make_shop(session, "Shop A")
    product = make_product(session, "Milo 400g")
    make_inventory(session, shop, product, 50)
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop)
    token = get_token(client, "mgr@example.com")

    resp = _post(client, token, _inventory_payload(product.id, 2, "16.00"))
    assert resp.status_code == 201
    assert resp.get_json()["purchase"]["shop_id"] == shop.id


def test_staff_can_make_inventory_purchase(session, client):
    shop = make_shop(session, "Shop A")
    product = make_product(session, "Milo 400g")
    make_inventory(session, shop, product, 50)
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    token = get_token(client, "staff@example.com")

    resp = _post(client, token, _inventory_payload(product.id, 1, "17.00"))
    assert resp.status_code == 201
    assert resp.get_json()["purchase"]["shop_id"] == shop.id


def test_staff_cannot_use_another_shops_inventory(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    product = make_product(session, "Milo 400g")
    make_inventory(session, shop_b, product, 50)
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop_a)
    token = get_token(client, "staff@example.com")

    resp = _post(client, token, _inventory_payload(product.id, 3, "18.00"))
    assert resp.status_code == 400
    assert "Insufficient stock" in resp.get_json()["error"]
    # Shop B stock unchanged.
    inv_b = ShopInventory.query.filter_by(product_id=product.id, shop_id=shop_b.id).first()
    assert inv_b.quantity == 50


def test_manager_cannot_use_another_shops_inventory(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    product = make_product(session, "Milo 400g")
    make_inventory(session, shop_b, product, 50)
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)
    token = get_token(client, "mgr@example.com")

    resp = _post(client, token, _inventory_payload(product.id, 3, "18.00"))
    assert resp.status_code == 400
    inv_b = ShopInventory.query.filter_by(product_id=product.id, shop_id=shop_b.id).first()
    assert inv_b.quantity == 50


def test_super_admin_can_select_authorized_shop(session, client):
    token = super_admin_token(session, client)
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    product = make_product(session, "Milo 400g")
    make_inventory(session, shop_a, product, 50)
    make_inventory(session, shop_b, product, 20)

    resp = _post(client, token, _inventory_payload(product.id, 5, "18.00", shop_b.id))
    assert resp.status_code == 201
    assert resp.get_json()["purchase"]["shop_id"] == shop_b.id
    inv_a = ShopInventory.query.filter_by(product_id=product.id, shop_id=shop_a.id).first()
    inv_b = ShopInventory.query.filter_by(product_id=product.id, shop_id=shop_b.id).first()
    assert inv_a.quantity == 50
    assert inv_b.quantity == 15


# --- stock ---


def test_purchase_deducts_correct_quantity(session, client):
    token, shop, product = _setup_product_with_stock(session, client, stock=50)
    _post(client, token, _inventory_payload(product.id, 3, "18.00", shop.id))

    inv = ShopInventory.query.filter_by(product_id=product.id, shop_id=shop.id).first()
    assert inv.quantity == 47


def test_stock_movement_before_change_after_correct(session, client):
    token, shop, product = _setup_product_with_stock(session, client, stock=50)
    _post(client, token, _inventory_payload(product.id, 3, "18.00", shop.id))

    movement = StockMovement.query.filter_by(
        product_id=product.id, shop_id=shop.id, movement_type=StockMovementType.SALE
    ).first()
    assert movement is not None
    assert movement.quantity_before == 50
    assert movement.quantity_change == -3
    assert movement.quantity_after == 47


def test_movement_type_is_sale(session, client):
    token, shop, product = _setup_product_with_stock(session, client, stock=50)
    _post(client, token, _inventory_payload(product.id, 3, "18.00", shop.id))

    movement = StockMovement.query.filter_by(product_id=product.id, shop_id=shop.id).first()
    assert movement.movement_type == StockMovementType.SALE
    assert movement.reference_id is not None


def test_actor_recorded_on_sale_movement(session, client):
    token, shop, product = _setup_product_with_stock(session, client, stock=50)
    admin = User.query.filter_by(email="admin@example.com").first()

    _post(client, token, _inventory_payload(product.id, 3, "18.00", shop.id))

    movement = StockMovement.query.filter_by(product_id=product.id, shop_id=shop.id).first()
    assert movement.actor_id == admin.id


def test_stock_never_becomes_negative(session, client):
    token, shop, product = _setup_product_with_stock(session, client, stock=2)
    resp = _post(client, token, _inventory_payload(product.id, 3, "18.00", shop.id))
    assert resp.status_code == 400

    inv = ShopInventory.query.filter_by(product_id=product.id, shop_id=shop.id).first()
    assert inv.quantity == 2
    assert Purchase.query.count() == 0


def test_zero_stock_rejects_sale(session, client):
    token, shop, product = _setup_product_with_stock(session, client, stock=0)
    resp = _post(client, token, _inventory_payload(product.id, 1, "18.00", shop.id))
    assert resp.status_code == 400
    assert "Insufficient stock" in resp.get_json()["error"]


def test_insufficient_stock_rejects_sale(session, client):
    token, shop, product = _setup_product_with_stock(session, client, stock=2)
    resp = _post(client, token, _inventory_payload(product.id, 3, "18.00", shop.id))
    assert resp.status_code == 400
    assert "Available: 2, requested: 3" in resp.get_json()["error"]
    assert Purchase.query.count() == 0
    inv = ShopInventory.query.filter_by(product_id=product.id, shop_id=shop.id).first()
    assert inv.quantity == 2


def test_inactive_product_rejects_sale(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    product = make_product(session, "Milo 400g", status="INACTIVE")
    make_inventory(session, shop, product, 50)

    resp = _post(client, token, _inventory_payload(product.id, 3, "18.00", shop.id))
    assert resp.status_code == 400
    assert Purchase.query.count() == 0
    inv = ShopInventory.query.filter_by(product_id=product.id, shop_id=shop.id).first()
    assert inv.quantity == 50


# --- price ---


def test_price_at_minimum_accepted(session, client):
    token, shop, product = _setup_product_with_stock(session, client)
    resp = _post(client, token, _inventory_payload(product.id, 1, "15.00", shop.id))
    assert resp.status_code == 201
    assert resp.get_json()["purchase"]["unit_price"] == "15.00"


def test_price_at_maximum_accepted(session, client):
    token, shop, product = _setup_product_with_stock(session, client)
    resp = _post(client, token, _inventory_payload(product.id, 1, "20.00", shop.id))
    assert resp.status_code == 201
    assert resp.get_json()["purchase"]["unit_price"] == "20.00"


def test_price_below_minimum_rejected(session, client):
    token, shop, product = _setup_product_with_stock(session, client)
    resp = _post(client, token, _inventory_payload(product.id, 1, "14.99", shop.id))
    assert resp.status_code == 400
    assert Purchase.query.count() == 0


def test_price_above_maximum_rejected(session, client):
    token, shop, product = _setup_product_with_stock(session, client)
    resp = _post(client, token, _inventory_payload(product.id, 1, "20.01", shop.id))
    assert resp.status_code == 400
    assert Purchase.query.count() == 0


def test_server_calculates_total_amount(session, client):
    token, shop, product = _setup_product_with_stock(session, client)
    resp = _post(client, token, _inventory_payload(product.id, 3, "18.00", shop.id))
    assert resp.status_code == 201
    assert resp.get_json()["purchase"]["amount"] == "54.00"


def test_client_cannot_manipulate_total_amount(session, client):
    token, shop, product = _setup_product_with_stock(session, client)
    payload = _inventory_payload(product.id, 3, "18.00", shop.id)
    payload["amount"] = "1.00"
    resp = _post(client, token, payload)
    assert resp.status_code == 201
    assert resp.get_json()["purchase"]["amount"] == "54.00"


# --- quantity ---


def test_quantity_of_one_works(session, client):
    token, shop, product = _setup_product_with_stock(session, client, stock=10)
    resp = _post(client, token, _inventory_payload(product.id, 1, "18.00", shop.id))
    assert resp.status_code == 201
    assert resp.get_json()["purchase"]["quantity"] == 1


def test_quantity_greater_than_one_works(session, client):
    token, shop, product = _setup_product_with_stock(session, client, stock=10)
    resp = _post(client, token, _inventory_payload(product.id, 5, "18.00", shop.id))
    assert resp.status_code == 201
    assert resp.get_json()["purchase"]["quantity"] == 5


def test_zero_quantity_rejected(session, client):
    token, shop, product = _setup_product_with_stock(session, client)
    resp = _post(client, token, _inventory_payload(product.id, 0, "18.00", shop.id))
    assert resp.status_code == 400


def test_negative_quantity_rejected(session, client):
    token, shop, product = _setup_product_with_stock(session, client)
    resp = _post(client, token, _inventory_payload(product.id, -1, "18.00", shop.id))
    assert resp.status_code == 400


def test_invalid_quantity_rejected(session, client):
    token, shop, product = _setup_product_with_stock(session, client)
    resp = _post(client, token, _inventory_payload(product.id, "abc", "18.00", shop.id))
    assert resp.status_code == 400


def test_non_integer_quantity_rejected(session, client):
    token, shop, product = _setup_product_with_stock(session, client)
    resp = _post(client, token, _inventory_payload(product.id, 2.5, "18.00", shop.id))
    assert resp.status_code == 400


# --- transaction safety ---


def test_stock_validation_failure_creates_no_purchase(session, client):
    token, shop, product = _setup_product_with_stock(session, client, stock=2)
    _post(client, token, _inventory_payload(product.id, 3, "18.00", shop.id))

    assert Purchase.query.count() == 0
    assert StockMovement.query.filter_by(movement_type=StockMovementType.SALE).count() == 0


def test_purchase_creation_failure_leaves_inventory_unchanged(session, client):
    token, shop, product = _setup_product_with_stock(session, client, stock=50)
    payload = _inventory_payload(product.id, 3, "18.00", shop.id)
    payload["customer"] = {"name": "No Phone"}
    resp = _post(client, token, payload)
    assert resp.status_code == 400

    inv = ShopInventory.query.filter_by(product_id=product.id, shop_id=shop.id).first()
    assert inv.quantity == 50
    assert Purchase.query.count() == 0


def test_inventory_update_failure_rolls_back_purchase(session, client, monkeypatch):
    from app.extensions import db

    token, shop, product = _setup_product_with_stock(session, client, stock=50)

    def failing_commit():
        raise RuntimeError("simulated commit failure")

    monkeypatch.setattr(db.session, "commit", failing_commit)

    resp = _post(client, token, _inventory_payload(product.id, 3, "18.00", shop.id))
    assert resp.status_code == 500

    inv = ShopInventory.query.filter_by(product_id=product.id, shop_id=shop.id).first()
    assert inv.quantity == 50
    assert Purchase.query.count() == 0


def test_purchase_and_stock_commit_together(session, client):
    token, shop, product = _setup_product_with_stock(session, client, stock=50)
    resp = _post(client, token, _inventory_payload(product.id, 3, "18.00", shop.id))
    assert resp.status_code == 201

    assert Purchase.query.count() == 1
    inv = ShopInventory.query.filter_by(product_id=product.id, shop_id=shop.id).first()
    assert inv.quantity == 47
    movement = StockMovement.query.filter_by(
        product_id=product.id, shop_id=shop.id, movement_type=StockMovementType.SALE
    ).first()
    assert movement is not None


# --- SMS ---


def test_successful_purchase_triggers_sms(session, client):
    make_template(session)
    token, shop, product = _setup_product_with_stock(session, client)
    resp = _post(client, token, _inventory_payload(product.id, 3, "18.00", shop.id))
    assert resp.status_code == 201
    assert resp.get_json()["sms"]["status"] == SMSStatus.SENT
    assert SMSLog.query.count() == 1


def test_sms_failure_does_not_rollback_purchase(session, client, app):
    make_template(session)
    token, shop, product = _setup_product_with_stock(session, client)
    app.config["SMS_MOCK_FAIL"] = True

    resp = _post(client, token, _inventory_payload(product.id, 3, "18.00", shop.id))
    assert resp.status_code == 201
    assert resp.get_json()["sms"]["status"] == SMSStatus.FAILED
    assert Purchase.query.count() == 1


def test_sms_failure_does_not_restore_inventory(session, client, app):
    make_template(session)
    token, shop, product = _setup_product_with_stock(session, client, stock=50)
    app.config["SMS_MOCK_FAIL"] = True

    _post(client, token, _inventory_payload(product.id, 3, "18.00", shop.id))

    inv = ShopInventory.query.filter_by(product_id=product.id, shop_id=shop.id).first()
    assert inv.quantity == 47
    assert StockMovement.query.filter_by(movement_type=StockMovementType.SALE).count() == 1


def test_failed_sms_remains_retryable(session, client, app):
    make_template(session)
    token, shop, product = _setup_product_with_stock(session, client)
    app.config["SMS_MOCK_FAIL"] = True

    _post(client, token, _inventory_payload(product.id, 3, "18.00", shop.id))
    sms = SMSLog.query.first()
    assert sms.status == SMSStatus.FAILED

    app.config["SMS_MOCK_FAIL"] = False
    retry = client.post(f"/api/sms/{sms.id}/retry", headers=auth_header(token))
    assert retry.status_code == 200
    assert retry.get_json()["sms"]["status"] == SMSStatus.SENT


# --- authorization / spoofing ---


def test_manager_cannot_create_products_through_purchase(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop)
    token = get_token(client, "mgr@example.com")

    resp = _post(client, token, _inventory_payload("nonexistent-product-id", 1, "18.00"))
    assert resp.status_code == 404
    assert Product.query.count() == 0


def test_staff_cannot_create_products_through_purchase(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    token = get_token(client, "staff@example.com")

    resp = _post(client, token, _inventory_payload("nonexistent-product-id", 1, "18.00"))
    assert resp.status_code == 404
    assert Product.query.count() == 0


def test_client_cannot_spoof_staff_id(session, client):
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    product = make_product(session, "Milo 400g")
    make_inventory(session, shop, product, 50)
    token = get_token(client, "staff@example.com")

    payload = _inventory_payload(product.id, 1, "18.00")
    payload["staff_id"] = "someone-else"
    resp = _post(client, token, payload)
    assert resp.status_code == 400

    # A valid request still attributes the authenticated user.
    resp = _post(client, token, _inventory_payload(product.id, 1, "18.00"))
    assert resp.status_code == 201
    assert resp.get_json()["purchase"]["staff_id"] == staff.id


def test_client_cannot_spoof_shop_id_for_manager(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    product = make_product(session, "Milo 400g")
    make_inventory(session, shop_a, product, 50)
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)
    token = get_token(client, "mgr@example.com")

    resp = _post(client, token, _inventory_payload(product.id, 3, "18.00", shop_b.id))
    assert resp.status_code == 403
    inv_a = ShopInventory.query.filter_by(product_id=product.id, shop_id=shop_a.id).first()
    assert inv_a.quantity == 50


def test_client_cannot_spoof_shop_id_for_staff(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    product = make_product(session, "Milo 400g")
    make_inventory(session, shop_a, product, 50)
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop_a)
    token = get_token(client, "staff@example.com")

    resp = _post(client, token, _inventory_payload(product.id, 3, "18.00", shop_b.id))
    assert resp.status_code == 403
    inv_a = ShopInventory.query.filter_by(product_id=product.id, shop_id=shop_a.id).first()
    assert inv_a.quantity == 50


def test_client_cannot_modify_another_shops_inventory(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    product = make_product(session, "Milo 400g")
    make_inventory(session, shop_a, product, 50)
    make_inventory(session, shop_b, product, 30)
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop_a)
    token = get_token(client, "staff@example.com")

    # staff buys from own shop -> only shop A is affected
    resp = _post(client, token, _inventory_payload(product.id, 2, "18.00"))
    assert resp.status_code == 201

    inv_a = ShopInventory.query.filter_by(product_id=product.id, shop_id=shop_a.id).first()
    inv_b = ShopInventory.query.filter_by(product_id=product.id, shop_id=shop_b.id).first()
    assert inv_a.quantity == 48
    assert inv_b.quantity == 30


# --- backward compatibility ---


def test_legacy_purchase_still_works_without_inventory(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")

    resp = _post(
        client,
        token,
        {"shop_id": shop.id, "customer": _customer(), "product": "Rice 5kg", "amount": 150.00},
    )
    assert resp.status_code == 201
    body = resp.get_json()["purchase"]
    assert body["product"] == "Rice 5kg"
    assert body["product_id"] is None
    assert body["quantity"] is None
    assert body["unit_price"] is None
    assert ShopInventory.query.count() == 0
    assert StockMovement.query.count() == 0


def test_legacy_purchase_with_quantity_but_no_product_id_rejected(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")

    resp = _post(
        client,
        token,
        {"shop_id": shop.id, "customer": _customer(), "product": "Rice", "amount": 10, "quantity": 2},
    )
    assert resp.status_code == 400


def test_sale_movement_reference_matches_purchase(session, client):
    token, shop, product = _setup_product_with_stock(session, client, stock=50)
    resp = _post(client, token, _inventory_payload(product.id, 3, "18.00", shop.id))
    purchase_id = resp.get_json()["purchase"]["id"]

    movement = StockMovement.query.filter_by(movement_type=StockMovementType.SALE).first()
    assert movement.reference_id == purchase_id
    assert movement.quantity_change == -3


def test_remaining_stock_reported_after_sale(session, client):
    make_template(session)
    token, shop, product = _setup_product_with_stock(session, client, stock=50)
    resp = _post(client, token, _inventory_payload(product.id, 3, "18.00", shop.id))
    assert resp.status_code == 201
    assert resp.get_json()["purchase"]["remaining_stock"] == 47
