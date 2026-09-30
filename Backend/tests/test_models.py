from decimal import Decimal

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import (
    AuditLog,
    Customer,
    Purchase,
    Shop,
    ShopStatus,
    SMSLog,
    SMSStatus,
    SMSTemplate,
    User,
    UserRole,
)


def test_expected_tables_exist(app):
    with app.app_context():
        inspector = inspect(db.engine)
        tables = set(inspector.get_table_names())

    expected = {
        "shops",
        "users",
        "customers",
        "purchases",
        "sms_logs",
        "sms_templates",
        "audit_logs",
    }
    assert expected.issubset(tables)


def test_shop_can_be_created(session):
    shop = Shop(name="Test Shop", status=ShopStatus.ACTIVE)
    session.add(shop)
    session.commit()

    assert Shop.query.count() == 1
    assert Shop.query.first().name == "Test Shop"
    assert Shop.query.first().status == ShopStatus.ACTIVE


def test_customer_can_be_created(session):
    customer = Customer(name="John Mensah", phone="0240000000")
    session.add(customer)
    session.commit()

    assert Customer.query.count() == 1
    assert Customer.query.first().phone == "0240000000"


def test_purchase_relationships(session):
    shop = Shop(name="Main", status=ShopStatus.ACTIVE)
    staff = User(
        name="John",
        email="john@example.com",
        password_hash="hash",
        role=UserRole.STAFF,
        shop=shop,
    )
    customer = Customer(name="John Mensah", phone="0240000000")
    session.add_all([shop, staff, customer])
    session.commit()

    purchase = Purchase(
        shop=shop,
        staff=staff,
        customer=customer,
        product="Samsung A25",
        amount=Decimal("3500.00"),
    )
    session.add(purchase)
    session.commit()

    loaded = Purchase.query.first()
    assert loaded.shop.id == shop.id
    assert loaded.staff.id == staff.id
    assert loaded.customer.id == customer.id
    assert loaded.amount == Decimal("3500.00")
    assert loaded.currency == "GHS"


def test_sms_log_associated_with_purchase(session):
    shop = Shop(name="Main", status=ShopStatus.ACTIVE)
    staff = User(
        name="John",
        email="john2@example.com",
        password_hash="hash",
        role=UserRole.STAFF,
        shop=shop,
    )
    customer = Customer(name="Ama", phone="0240000001")
    session.add_all([shop, staff, customer])
    session.commit()

    purchase = Purchase(
        shop=shop,
        staff=staff,
        customer=customer,
        product="Samsung A25",
        amount=Decimal("3500.00"),
    )
    session.add(purchase)
    session.commit()

    sms = SMSLog(
        shop=shop,
        purchase=purchase,
        customer=customer,
        phone_number="0240000001",
        message="Congratulations Ama!",
        status=SMSStatus.PENDING,
    )
    session.add(sms)
    session.commit()

    loaded = SMSLog.query.first()
    assert loaded.purchase.id == purchase.id
    assert loaded.status == SMSStatus.PENDING
    assert purchase.sms_logs == [loaded]


def test_negative_purchase_amount_rejected(session):
    shop = Shop(name="Main", status=ShopStatus.ACTIVE)
    staff = User(
        name="John",
        email="john3@example.com",
        password_hash="hash",
        role=UserRole.STAFF,
        shop=shop,
    )
    customer = Customer(name="Kwame", phone="0240000002")
    session.add_all([shop, staff, customer])
    session.commit()

    purchase = Purchase(
        shop=shop,
        staff=staff,
        customer=customer,
        product="X",
        amount=Decimal("-5.00"),
    )
    session.add(purchase)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_user_email_is_unique(session):
    shop = Shop(name="Main", status=ShopStatus.ACTIVE)
    first = User(
        name="A",
        email="dup@example.com",
        password_hash="hash",
        role=UserRole.STAFF,
        shop=shop,
    )
    session.add_all([shop, first])
    session.commit()

    duplicate = User(
        name="B",
        email="dup@example.com",
        password_hash="hash",
        role=UserRole.STAFF,
        shop=shop,
    )
    session.add(duplicate)
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_super_admin_has_no_shop(session):
    admin = User(
        name="Owner",
        email="owner@example.com",
        password_hash="hash",
        role=UserRole.SUPER_ADMIN,
    )
    session.add(admin)
    session.commit()

    loaded = User.query.filter_by(email="owner@example.com").first()
    assert loaded.shop_id is None


def test_template_and_audit_log_can_be_created(session):
    admin = User(
        name="Owner",
        email="owner2@example.com",
        password_hash="hash",
        role=UserRole.SUPER_ADMIN,
    )
    session.add(admin)
    session.commit()

    template = SMSTemplate(
        name="Purchase",
        message="Congratulations {name}!",
        is_active=True,
        creator=admin,
    )
    log = AuditLog(
        user=admin,
        action="template.created",
        entity_type="sms_template",
        entity_id=template.id,
        description="Created purchase template",
    )
    session.add_all([template, log])
    session.commit()

    assert SMSTemplate.query.count() == 1
    assert AuditLog.query.count() == 1
    assert AuditLog.query.first().user.id == admin.id
