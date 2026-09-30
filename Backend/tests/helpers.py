from decimal import Decimal

from werkzeug.security import generate_password_hash

from app.models import Customer, Purchase, Shop, ShopStatus, User, UserRole, UserStatus


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


def make_customer(session, name, phone, email=None):
    customer = Customer(name=name, phone=phone, email=email)
    session.add(customer)
    session.commit()
    return customer


def make_purchase(session, shop, staff, customer, product="Rice", amount=Decimal("100.00"), created_at=None):
    purchase = Purchase(
        shop_id=shop.id,
        staff_id=staff.id,
        customer_id=customer.id,
        product=product,
        amount=amount,
        currency="GHS",
        created_at=created_at,
    )
    session.add(purchase)
    session.commit()
    return purchase
