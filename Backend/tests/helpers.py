from werkzeug.security import generate_password_hash

from app.models import Shop, ShopStatus, User, UserRole, UserStatus


def make_shop(session, name, status=ShopStatus.ACTIVE, **kwargs):
    shop = Shop(name=name, status=status, **kwargs)
    session.add(shop)
    session.commit()
    return shop


def make_user(
    session,
    role,
    email,
    password="password123",
    shop=None,
    status=UserStatus.ACTIVE,
    name=None,
):
    user = User(
        name=name or email.split("@")[0],
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
    return client.post("/api/auth/login", json={"email": email, "password": password})


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def get_token(client, email, password="password123"):
    return login(client, email, password).get_json()["access_token"]


def super_admin_token(session, client, email="admin@example.com"):
    make_user(session, UserRole.SUPER_ADMIN, email)
    return get_token(client, email)
