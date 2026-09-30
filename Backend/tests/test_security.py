from app.models import UserRole
from tests.helpers import auth_header, get_token, make_shop, make_user, super_admin_token


def test_missing_jwt_rejected(client):
    resp = client.get("/api/shops")
    assert resp.status_code == 401


def test_invalid_jwt_rejected(client):
    resp = client.get("/api/shops", headers=auth_header("invalid-token"))
    assert resp.status_code == 401


def test_role_restrictions_enforced(session, client):
    shop = make_shop(session, "Shop A")
    make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    token = get_token(client, "staff@example.com")

    # Staff cannot list users (management endpoint).
    assert client.get("/api/users", headers=auth_header(token)).status_code == 403
    # Staff cannot create users.
    assert client.post("/api/users", headers=auth_header(token), json={}).status_code == 403


def test_cross_shop_access_rejected(session, client):
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    make_user(session, UserRole.SHOP_MANAGER, "mgr@example.com", shop=shop_a)
    make_user(session, UserRole.STAFF, "other@example.com", shop=shop_b)
    token = get_token(client, "mgr@example.com")

    # Manager cannot fetch another shop's user record.
    from app.models import User

    other = User.query.filter_by(email="other@example.com").first()
    resp = client.get(f"/api/users/{other.id}", headers=auth_header(token))
    assert resp.status_code == 403
