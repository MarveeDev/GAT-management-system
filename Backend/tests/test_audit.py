from app.models import AuditLog, UserRole
from app.services.audit_service import AuditAction
from tests.helpers import auth_header, get_token, make_shop, make_user, super_admin_token


def _count(action):
    return AuditLog.query.filter_by(action=action).count()


def test_shop_creation_creates_audit_log(session, client):
    token = super_admin_token(session, client)
    client.post(
        "/api/shops",
        headers=auth_header(token),
        json={"name": "New Shop", "location": "Accra"},
    )
    assert _count(AuditAction.SHOP_CREATED) == 1


def test_shop_update_creates_audit_log(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    client.patch(f"/api/shops/{shop.id}", headers=auth_header(token), json={"name": "Renamed"})
    assert _count(AuditAction.SHOP_UPDATED) == 1


def test_shop_deactivation_creates_audit_log(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    client.patch(f"/api/shops/{shop.id}", headers=auth_header(token), json={"status": "INACTIVE"})
    assert _count(AuditAction.SHOP_DEACTIVATED) == 1


def test_user_creation_creates_audit_log(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    client.post(
        "/api/users",
        headers=auth_header(token),
        json={"name": "Staff", "email": "staff@example.com", "password": "secure-password", "role": "STAFF", "shop_id": shop.id},
    )
    logs = AuditLog.query.filter_by(action=AuditAction.USER_CREATED).all()
    assert len(logs) == 1
    assert logs[0].entity_type == "USER"
    assert logs[0].shop_id == shop.id


def test_user_role_change_creates_audit_log(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    client.patch(f"/api/users/{staff.id}", headers=auth_header(token), json={"role": "SHOP_MANAGER"})
    assert _count(AuditAction.USER_ROLE_CHANGED) == 1


def test_user_shop_change_creates_audit_log(session, client):
    token = super_admin_token(session, client)
    shop_a = make_shop(session, "Shop A")
    shop_b = make_shop(session, "Shop B")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop_a)
    client.patch(f"/api/users/{staff.id}", headers=auth_header(token), json={"shop_id": shop_b.id})
    assert _count(AuditAction.USER_SHOP_CHANGED) == 1


def test_password_reset_creates_audit_log(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    staff = make_user(session, UserRole.STAFF, "staff@example.com", shop=shop)
    client.patch(f"/api/users/{staff.id}/password", headers=auth_header(token), json={"password": "new-secure-password"})
    assert _count(AuditAction.USER_PASSWORD_RESET) == 1


def test_audit_logs_do_not_contain_passwords(session, client):
    token = super_admin_token(session, client)
    shop = make_shop(session, "Shop A")
    client.post(
        "/api/users",
        headers=auth_header(token),
        json={"name": "Staff", "email": "staff@example.com", "password": "secret-password", "role": "STAFF", "shop_id": shop.id},
    )
    staff = make_user(session, UserRole.STAFF, "staff2@example.com", shop=shop)
    client.patch(f"/api/users/{staff.id}/password", headers=auth_header(token), json={"password": "another-secret"})

    for log in AuditLog.query.all():
        text = (log.description or "") + (log.action or "")
        assert "secret-password" not in text
        assert "another-secret" not in text
