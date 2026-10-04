from decimal import Decimal

from werkzeug.security import generate_password_hash

from app.models import (
    Customer,
    Product,
    ProductStatus,
    Purchase,
    Shop,
    ShopInventory,
    ShopStatus,
    SMSLog,
    SMSTemplate,
    SMSStatus,
    StockMovement,
    StockMovementType,
    User,
    UserRole,
    UserStatus,
)


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


def make_template(session, name="PURCHASE_THANK_YOU", message=None, is_active=True):
    if message is None:
        message = (
            "Hi {{customer_name}}, thank you for purchasing {{product}} "
            "for GHS {{amount}} at {{shop_name}}."
        )
    template = SMSTemplate(name=name, message=message, is_active=is_active)
    session.add(template)
    session.commit()
    return template


def make_product(
    session,
    name,
    minimum_price=Decimal("15.00"),
    maximum_price=Decimal("20.00"),
    category=None,
    status=ProductStatus.ACTIVE,
):
    product = Product(
        name=name,
        category=category,
        minimum_price=minimum_price,
        maximum_price=maximum_price,
        status=status,
    )
    session.add(product)
    session.commit()
    return product


def make_inventory(session, shop, product, quantity=0):
    inventory = ShopInventory(shop_id=shop.id, product_id=product.id, quantity=quantity)
    session.add(inventory)
    session.commit()
    return inventory


def make_stock_movement(
    session,
    shop,
    product,
    quantity_change,
    quantity_before,
    quantity_after,
    movement_type=StockMovementType.MANUAL_ADJUSTMENT,
    actor=None,
    reference_id=None,
):
    movement = StockMovement(
        product_id=product.id,
        shop_id=shop.id,
        quantity_change=quantity_change,
        quantity_before=quantity_before,
        quantity_after=quantity_after,
        movement_type=movement_type,
        reference_id=reference_id,
        actor_id=actor.id if actor else None,
    )
    session.add(movement)
    session.commit()
    return movement


def make_sms_log(
    session,
    shop,
    purchase,
    customer,
    status=SMSStatus.FAILED,
    phone="233240000000",
    message="Hello",
    created_at=None,
    error_message=None,
):
    sms_log = SMSLog(
        shop_id=shop.id,
        purchase_id=purchase.id,
        customer_id=customer.id,
        phone_number=phone,
        message=message,
        provider="mock",
        status=status,
        created_at=created_at,
        error_message=error_message,
    )
    session.add(sms_log)
    session.commit()
    return sms_log
