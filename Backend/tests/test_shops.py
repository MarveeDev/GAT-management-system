from tests.helpers import (
    auth_header,
    get_token,
    make_shop,
    make_user,
    super_admin_token,
)
from app.models import Shop, ShopStatus, UserRole


def _create_shops(session):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    return shop_a, shop_b


# --- listing ---


def test_super_admin_can_list_shops(session, client):
    token = super_admin_token(session, client)
    make_shop(session, "Shop A")
    make_shop(session, "Shop B")

    resp = client.get("/api/shops", headers=auth_header(token))
    assert resp.status_code == 200
    names = [s["name"] for s in resp.get_json()["shops"]]
    assert "Shop A" in names and "Shop B" in names


def test_shop_manager_sees_only_own_shop(session, client):
    shop_a, shop_b = _create_shops(session)
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)
    token = get_token(client, "mgr@example.com")

    resp = client.get("/api/shops", headers=auth_header(token))
    assert resp.status_code == 200
    shops = resp.get_json()["shops"]
    assert len(shops) == 1
    assert shops[0]["id"] == shop_a.id


def test_staff_sees_only_own_shop(session, client):
    shop_a, shop_b = _create_shops(session)
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop_a)
    token = get_token(client, "staff@example.com")

    resp = client.get("/api/shops", headers=auth_header(token))
    assert resp.status_code == 200
    shops = resp.get_json()["shops"]
    assert len(shops) == 1
    assert shops[0]["id"] == shop_a.id


# --- create ---


def test_super_admin_can_create_shop(session, client):
    token = super_admin_token(session, client)
    resp = client.post(
        "/api/shops",
        headers=auth_header(token),
        json={"name": "New Shop", "location": "Accra", "phone": "0240000000", "sender_id": "GREAT"},
    )
    assert resp.status_code == 201
    body = resp.get_json()["shop"]
    assert body["name"] == "New Shop"
    assert body["status"] == "ACTIVE"
    assert "password_hash" not in body


def test_create_shop_requires_name(session, client):
    token = super_admin_token(session, client)
    resp = client.post("/api/shops", headers=auth_header(token), json={"location": "Accra"})
    assert resp.status_code == 400


def test_non_super_admin_cannot_create_shop(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop)
    token = get_token(client, "mgr@example.com")

    resp = client.post(
        "/api/shops",
        headers=auth_header(token),
        json={"name": "Evil Shop"},
    )
    assert resp.status_code == 403


def test_create_shop_rejects_unknown_fields(session, client):
    token = super_admin_token(session, client)
    resp = client.post(
        "/api/shops",
        headers=auth_header(token),
        json={"name": "Shop", "bogus": "value"},
    )
    assert resp.status_code == 400


# --- update / deactivate ---


def test_super_admin_can_update_shop(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")

    resp = client.patch(
        f"/api/shops/{shop.id}",
        headers=auth_header(token),
        json={"name": "Shop A Renamed", "location": "Kumasi"},
    )
    assert resp.status_code == 200
    assert resp.get_json()["shop"]["name"] == "Shop A Renamed"


def test_super_admin_can_deactivate_and_reactivate_shop(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")

    resp = client.patch(
        f"/api/shops/{shop.id}", headers=auth_header(token), json={"status": "INACTIVE"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["shop"]["status"] == "INACTIVE"

    resp = client.patch(
        f"/api/shops/{shop.id}", headers=auth_header(token), json={"status": "ACTIVE"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["shop"]["status"] == "ACTIVE"


def test_update_shop_invalid_status(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    resp = client.patch(
        f"/api/shops/{shop.id}", headers=auth_header(token), json={"status": "BOGUS"}
    )
    assert resp.status_code == 400


# --- get single shop ---


def test_super_admin_can_view_any_shop(session, client):
    token = super_admin_token(session, client)
    shop_a, shop_b = _create_shops(session)
    resp = client.get(f"/api/shops/{shop_b.id}", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.get_json()["shop"]["id"] == shop_b.id


def test_shop_manager_cannot_access_another_shop(session, client):
    shop_a, shop_b = _create_shops(session)
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)
    token = get_token(client, "mgr@example.com")

    resp = client.get(f"/api/shops/{shop_b.id}", headers=auth_header(token))
    assert resp.status_code == 403


def test_staff_cannot_access_another_shop(session, client):
    shop_a, shop_b = _create_shops(session)
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop_a)
    token = get_token(client, "staff@example.com")

    resp = client.get(f"/api/shops/{shop_b.id}", headers=auth_header(token))
    assert resp.status_code == 403


def test_get_nonexistent_shop_returns_404(session, client):
    token = super_admin_token(session, client)
    resp = client.get("/api/shops/nonexistent-id", headers=auth_header(token))
    assert resp.status_code == 404


def test_shops_are_not_physically_deleted(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    resp = client.delete(f"/api/shops/{shop.id}", headers=auth_header(token))
    assert resp.status_code == 405

    # Shop still exists.
    assert session.get(Shop, shop.id) is not None


def test_shop_patch_requires_super_admin(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop)
    token = get_token(client, "mgr@example.com")

    resp = client.patch(f"/api/shops/{shop.id}", headers=auth_header(token), json={"name": "X"})
    assert resp.status_code == 403
