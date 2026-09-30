import pytest
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import Shop, ShopStatus, User, UserRole, UserStatus
from app.services.user_service import create_super_admin
from app.utils.auth import has_shop_access
from app.utils.validators import validate_shop_assignment


def make_shop(session, name):
    shop = Shop(name=name, status=ShopStatus.ACTIVE)
    session.add(shop)
    session.commit()
    return shop


def make_user(session, role, email, password="password123", shop=None, status=UserStatus.ACTIVE):
    user = User(
        name=email.split("@")[0],
        email=email,
        phone="0240000000",
        password_hash=generate_password_hash(password),
        role=role,
        shop=shop,
        status=status,
    )
    session.add(user)
    session.commit()
    return user


def login(client, email, password="password123"):
    return client.post(
        "/api/auth/login", json={"email": email, "password": password}
    )


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


# --- login ---


def test_login_valid_super_admin(session, client):
    make_user(session, UserRole.SUPER_ADMIN, "admin@example.com")
    resp = login(client, "admin@example.com")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["access_token"]
    assert data["user"]["role"] == "SUPER_ADMIN"
    assert data["user"]["shop_id"] is None
    assert data["user"]["email"] == "admin@example.com"


def test_login_returns_shop_id_for_shop_user(session, client):
    shop = make_shop(session, "Main")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    resp = login(client, "staff@example.com")
    assert resp.status_code == 200
    assert resp.get_json()["user"]["shop_id"] == shop.id


def test_login_incorrect_password(session, client):
    make_user(session, UserRole.SUPER_ADMIN, "admin@example.com")
    resp = login(client, "admin@example.com", password="wrong-password")
    assert resp.status_code == 401
    assert resp.get_json()["message"] == "Invalid email or password."


def test_login_unknown_email(client):
    resp = login(client, "nobody@example.com")
    assert resp.status_code == 401
    assert resp.get_json()["message"] == "Invalid email or password."


def test_login_does_not_reveal_email_existence(session, client):
    make_user(session, UserRole.SUPER_ADMIN, "admin@example.com")
    wrong_pw = login(client, "admin@example.com", password="wrong")
    unknown = login(client, "ghost@example.com")
    assert wrong_pw.get_json()["message"] == unknown.get_json()["message"]


def test_login_inactive_user(session, client):
    make_user(session, UserRole.SUPER_ADMIN, "admin@example.com", status=UserStatus.INACTIVE)
    resp = login(client, "admin@example.com")
    assert resp.status_code == 403


def test_login_malformed_body(client):
    resp = client.post("/api/auth/login", data="not-json", content_type="text/plain")
    assert resp.status_code == 400


def test_login_missing_fields(client):
    resp = client.post("/api/auth/login", json={"email": "a@b.com"})
    assert resp.status_code == 400


# --- password hashing ---


def test_password_is_hashed(session):
    user = make_user(session, UserRole.SUPER_ADMIN, "admin@example.com")
    assert user.password_hash != "password123"
    assert check_password_hash(user.password_hash, "password123")


def test_serialization_never_exposes_password_hash(session):
    user = make_user(session, UserRole.SUPER_ADMIN, "admin@example.com")
    data = user.to_dict()
    assert "password_hash" not in data
    assert "password" not in data
    assert data["email"] == "admin@example.com"


# --- /api/auth/me ---


def test_me_with_valid_jwt(session, client):
    make_user(session, UserRole.SUPER_ADMIN, "admin@example.com")
    token = login(client, "admin@example.com").get_json()["access_token"]
    resp = client.get("/api/auth/me", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.get_json()["user"]["email"] == "admin@example.com"
    assert "password_hash" not in resp.get_json()["user"]


def test_me_without_jwt(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_with_invalid_jwt(client):
    resp = client.get("/api/auth/me", headers=auth_header("not-a-valid-token"))
    assert resp.status_code == 401


def test_inactive_user_cannot_access_protected_route(session, client):
    shop = make_shop(session, "Main")
    user = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    token = login(client, "staff@example.com").get_json()["access_token"]

    user.status = UserStatus.INACTIVE
    session.commit()

    resp = client.get("/api/auth/me", headers=auth_header(token))
    assert resp.status_code == 401


# --- shop-level authorization ---


def test_super_admin_has_no_shop_restriction(session):
    admin = make_user(session, UserRole.SUPER_ADMIN, "admin@example.com")
    assert has_shop_access(admin, "any-shop-id") is True
    assert has_shop_access(admin, None) is True


def test_manager_cannot_access_another_shop(session):
    shop = make_shop(session, "Main")
    manager = make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop)
    assert has_shop_access(manager, shop.id) is True
    assert has_shop_access(manager, "other-shop-id") is False
    assert has_shop_access(manager, None) is False


def test_staff_cannot_access_another_shop(session):
    shop = make_shop(session, "Main")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    assert has_shop_access(staff, shop.id) is True
    assert has_shop_access(staff, "other-shop-id") is False


def test_super_admin_can_access_any_shop(session):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    admin = make_user(session, UserRole.SUPER_ADMIN, "admin@example.com")
    assert has_shop_access(admin, shop_a.id) is True
    assert has_shop_access(admin, shop_b.id) is True


# --- role/shop assignment validation ---


def test_super_admin_shop_may_be_null():
    assert validate_shop_assignment(UserRole.SUPER_ADMIN, None) is None


def test_shop_manager_requires_shop_id():
    assert validate_shop_assignment(UserRole.SHOP_MANAGER, None) is not None


def test_staff_requires_shop_id():
    assert validate_shop_assignment(UserRole.STAFF, "") is not None


# --- role authorization decorator ---


@pytest.fixture()
def protected_client(app):
    from app.utils.auth import roles_required

    @app.get("/api/_test/admin-only")
    @roles_required("SUPER_ADMIN")
    def admin_only():
        return {"ok": True}

    @app.get("/api/_test/staff-or-manager")
    @roles_required("STAFF", "SHOP_MANAGER")
    def staff_or_manager():
        return {"ok": True}

    return app.test_client()


def test_role_authorization_allows_permitted_role(session, protected_client):
    make_user(session, UserRole.SUPER_ADMIN, "admin@example.com")
    token = login(protected_client, "admin@example.com").get_json()["access_token"]
    resp = protected_client.get("/api/_test/admin-only", headers=auth_header(token))
    assert resp.status_code == 200


def test_role_authorization_rejects_unauthorized_role(session, protected_client):
    shop = make_shop(session, "Main")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    token = login(protected_client, "staff@example.com").get_json()["access_token"]
    resp = protected_client.get("/api/_test/admin-only", headers=auth_header(token))
    assert resp.status_code == 403


def test_role_authorization_rejects_missing_token(protected_client):
    resp = protected_client.get("/api/_test/admin-only")
    assert resp.status_code == 401


# --- seed admin service ---


def test_create_super_admin(session):
    user, error = create_super_admin("Owner", "owner@example.com", "", "password123")
    assert error is None
    assert user is not None
    assert user.role == UserRole.SUPER_ADMIN
    assert user.shop_id is None
    assert user.status == UserStatus.ACTIVE
    assert user.password_hash != "password123"
    assert check_password_hash(user.password_hash, "password123")


def test_create_super_admin_duplicate(session):
    create_super_admin("Owner", "owner@example.com", "", "password123")
    user, error = create_super_admin("Owner 2", "OWNER@example.com", "", "password456")
    assert user is None
    assert error is not None


def test_create_super_admin_invalid_input(session):
    user, error = create_super_admin("", "bad-email", "", "short")
    assert user is None
    assert error is not None


def test_create_super_admin_short_password(session):
    user, error = create_super_admin("Owner", "owner@example.com", "", "1234567")
    assert user is None
    assert error is not None
