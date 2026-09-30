from werkzeug.security import check_password_hash

from app.models import Shop, ShopStatus, User, UserRole, UserStatus
from tests.helpers import auth_header, get_token, make_shop, make_user, super_admin_token


# --- listing ---


def test_super_admin_can_list_all_users(session, client):
    token = super_admin_token(session, client)
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    make_user(session, UserRole.STAFF, "a@example.com", shop=shop_a)
    make_user(session, UserRole.STAFF, "b@example.com", shop=shop_b)

    resp = client.get("/api/users", headers=auth_header(token))
    assert resp.status_code == 200
    emails = [u["email"] for u in resp.get_json()["users"]]
    assert "a@example.com" in emails and "b@example.com" in emails


def test_super_admin_can_filter_users_by_shop(session, client):
    token = super_admin_token(session, client)
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    make_user(session, UserRole.STAFF, "a@example.com", shop=shop_a)
    make_user(session, UserRole.STAFF, "b@example.com", shop=shop_b)

    resp = client.get(f"/api/users?shop_id={shop_a.id}", headers=auth_header(token))
    assert resp.status_code == 200
    emails = [u["email"] for u in resp.get_json()["users"]]
    assert emails == ["a@example.com"]


def test_shop_manager_can_list_own_shop_users(session, client):
    shop_a, shop_b = make_shop(session, "Shop A"), make_shop(session, "Shop B")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)
    make_user(session, UserRole.STAFF, "a@example.com", shop=shop_a)
    make_user(session, UserRole.STAFF, "b@example.com", shop=shop_b)
    token = get_token(client, "mgr@example.com")

    resp = client.get("/api/users", headers=auth_header(token))
    assert resp.status_code == 200
    emails = [u["email"] for u in resp.get_json()["users"]]
    assert "a@example.com" in emails
    assert "b@example.com" not in emails
    assert "admin@example.com" not in emails  # no super admins leak


def test_shop_manager_cannot_list_users_from_another_shop(session, client):
    shop_a, shop_b = make_shop(session, "Shop A"), make_shop(session, "Shop B")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)
    make_user(session, UserRole.STAFF, "b@example.com", shop=shop_b)
    token = get_token(client, "mgr@example.com")

    # Even trying to filter by another shop must not leak that shop's users.
    resp = client.get(f"/api/users?shop_id={shop_b.id}", headers=auth_header(token))
    assert resp.status_code == 200
    emails = [u["email"] for u in resp.get_json()["users"]]
    assert "b@example.com" not in emails


# --- create ---


def test_super_admin_can_create_shop_manager(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")

    resp = client.post(
        "/api/users",
        headers=auth_header(token),
        json={
            "name": "Manager One",
            "email": "manager@example.com",
            "phone": "0240000000",
            "password": "secure-password",
            "role": "SHOP_MANAGER",
            "shop_id": shop.id,
        },
    )
    assert resp.status_code == 201
    body = resp.get_json()["user"]
    assert body["role"] == "SHOP_MANAGER"
    assert body["shop_id"] == shop.id
    assert "password_hash" not in body


def test_super_admin_can_create_staff(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")

    resp = client.post(
        "/api/users",
        headers=auth_header(token),
        json={
            "name": "Staff One",
            "email": "staff@example.com",
            "password": "secure-password",
            "role": "STAFF",
            "shop_id": shop.id,
        },
    )
    assert resp.status_code == 201
    assert resp.get_json()["user"]["role"] == "STAFF"


def test_shop_manager_can_create_staff_for_own_shop(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop)
    token = get_token(client, "mgr@example.com")

    resp = client.post(
        "/api/users",
        headers=auth_header(token),
        json={
            "name": "Staff One",
            "email": "staff@example.com",
            "password": "secure-password",
            "role": "STAFF",
            "shop_id": shop.id,
        },
    )
    assert resp.status_code == 201
    assert resp.get_json()["user"]["shop_id"] == shop.id


def test_shop_manager_cannot_create_shop_manager(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop)
    token = get_token(client, "mgr@example.com")

    resp = client.post(
        "/api/users",
        headers=auth_header(token),
        json={
            "name": "Manager",
            "email": "m2@example.com",
            "password": "secure-password",
            "role": "SHOP_MANAGER",
            "shop_id": shop.id,
        },
    )
    assert resp.status_code == 403


def test_shop_manager_cannot_create_staff_for_another_shop(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)
    token = get_token(client, "mgr@example.com")

    resp = client.post(
        "/api/users",
        headers=auth_header(token),
        json={
            "name": "Staff",
            "email": "staff@example.com",
            "password": "secure-password",
            "role": "STAFF",
            "shop_id": shop_b.id,
        },
    )
    assert resp.status_code == 403


def test_staff_cannot_create_users(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    token = get_token(client, "staff@example.com")

    resp = client.post(
        "/api/users",
        headers=auth_header(token),
        json={"name": "X", "email": "x@example.com", "password": "secure-password", "role": "STAFF", "shop_id": shop.id},
    )
    assert resp.status_code == 403


def test_create_user_requires_shop(session, client):
    token = super_admin_token(session, client)
    resp = client.post(
        "/api/users",
        headers=auth_header(token),
        json={"name": "X", "email": "x@example.com", "password": "secure-password", "role": "STAFF"},
    )
    assert resp.status_code == 400


def test_create_user_rejects_super_admin_role(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    resp = client.post(
        "/api/users",
        headers=auth_header(token),
        json={"name": "X", "email": "x@example.com", "password": "secure-password", "role": "SUPER_ADMIN", "shop_id": shop.id},
    )
    assert resp.status_code == 400


def test_create_user_duplicate_email(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.STAFF, "dup@example.com", shop=shop)

    resp = client.post(
        "/api/users",
        headers=auth_header(token),
        json={"name": "X", "email": "dup@example.com", "password": "secure-password", "role": "STAFF", "shop_id": shop.id},
    )
    assert resp.status_code == 409


def test_create_user_invalid_shop_id(session, client):
    token = super_admin_token(session, client)
    resp = client.post(
        "/api/users",
        headers=auth_header(token),
        json={"name": "X", "email": "x@example.com", "password": "secure-password", "role": "STAFF", "shop_id": "nonexistent"},
    )
    assert resp.status_code == 404


def test_create_user_inactive_shop_rejected(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A", status=ShopStatus.INACTIVE)

    resp = client.post(
        "/api/users",
        headers=auth_header(token),
        json={"name": "X", "email": "x@example.com", "password": "secure-password", "role": "STAFF", "shop_id": shop.id},
    )
    assert resp.status_code == 400


# --- update ---


def test_super_admin_can_update_user(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)

    resp = client.patch(
        f"/api/users/{staff.id}", headers=auth_header(token), json={"name": "Updated Name"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["user"]["name"] == "Updated Name"


def test_shop_manager_can_update_own_staff(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop)
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    token = get_token(client, "mgr@example.com")

    resp = client.patch(
        f"/api/users/{staff.id}", headers=auth_header(token), json={"name": "Renamed"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["user"]["name"] == "Renamed"


def test_shop_manager_cannot_modify_users_outside_shop(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)
    other = make_user(session, UserRole.STAFF, "other@example.com", shop=shop_b)
    token = get_token(client, "mgr@example.com")

    resp = client.patch(f"/api/users/{other.id}", headers=auth_header(token), json={"name": "X"})
    assert resp.status_code == 403


def test_shop_manager_cannot_promote_staff_to_manager(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop)
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    token = get_token(client, "mgr@example.com")

    resp = client.patch(
        f"/api/users/{staff.id}", headers=auth_header(token), json={"role": "SHOP_MANAGER"}
    )
    assert resp.status_code == 403


def test_staff_cannot_modify_other_users(session, client):
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    other = make_user(session, UserRole.STAFF, "other@example.com", shop=shop)
    token = get_token(client, "staff@example.com")

    resp = client.patch(f"/api/users/{other.id}", headers=auth_header(token), json={"name": "X"})
    assert resp.status_code == 403


def test_authorized_user_can_deactivate_user(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)

    resp = client.patch(
        f"/api/users/{staff.id}", headers=auth_header(token), json={"status": "INACTIVE"}
    )
    assert resp.status_code == 200
    assert resp.get_json()["user"]["status"] == "INACTIVE"


def test_inactive_user_cannot_login(session, client):
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop, status=UserStatus.INACTIVE)

    resp = client.post(
        "/api/auth/login", json={"email": "staff@example.com", "password": "password123"}
    )
    assert resp.status_code == 403


def test_super_admin_can_move_user_between_active_shops(session, client):
    token = super_admin_token(session, client)
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop_a)

    resp = client.patch(
        f"/api/users/{staff.id}", headers=auth_header(token), json={"shop_id": shop_b.id}
    )
    assert resp.status_code == 200
    assert resp.get_json()["user"]["shop_id"] == shop_b.id


def test_shop_manager_cannot_move_staff_to_another_shop(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop_a)
    token = get_token(client, "mgr@example.com")

    resp = client.patch(
        f"/api/users/{staff.id}", headers=auth_header(token), json={"shop_id": shop_b.id}
    )
    assert resp.status_code == 403


def test_cannot_set_role_to_super_admin(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)

    resp = client.patch(
        f"/api/users/{staff.id}", headers=auth_header(token), json={"role": "SUPER_ADMIN"}
    )
    assert resp.status_code == 403


def test_super_admin_cannot_demote_without_shop(session, client):
    # Changing a SUPER_ADMIN to STAFF without a shop is rejected.
    admin = make_user(session, UserRole.SUPER_ADMIN, "owner@example.com")
    token = get_token(client, "owner@example.com")

    resp = client.patch(
        f"/api/users/{admin.id}", headers=auth_header(token), json={"role": "STAFF"}
    )
    # STAFF requires a shop; without shop_id -> 400
    assert resp.status_code == 400


# --- password reset ---


def test_password_reset_hashes_password(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)

    resp = client.patch(
        f"/api/users/{staff.id}/password",
        headers=auth_header(token),
        json={"password": "new-secure-password"},
    )
    assert resp.status_code == 200

    refreshed = session.get(User, staff.id)
    assert refreshed.password_hash != "new-secure-password"
    assert check_password_hash(refreshed.password_hash, "new-secure-password")


def test_password_hash_never_returned(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)

    resp = client.get(f"/api/users/{staff.id}", headers=auth_header(token))
    assert "password_hash" not in resp.get_json()["user"]


def test_password_reset_short_password_rejected(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)

    resp = client.patch(
        f"/api/users/{staff.id}/password", headers=auth_header(token), json={"password": "short"}
    )
    assert resp.status_code == 400


def test_staff_cannot_reset_another_users_password(session, client):
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    other = make_user(session, UserRole.STAFF, "other@example.com", shop=shop)
    token = get_token(client, "staff@example.com")

    resp = client.patch(
        f"/api/users/{other.id}/password", headers=auth_header(token), json={"password": "new-secure-password"}
    )
    assert resp.status_code == 403
