import re

from sqlalchemy import func

from app.extensions import db
from app.models.customer import Customer
from app.models.purchase import Purchase
from app.models.user import User, UserRole

_NON_DIGIT = re.compile(r"\D")


def normalize_phone(phone) -> str | None:
    """Normalize a phone number to an international E.164-style form.

    Ghanaian examples handled:

    - ``0240000000``   -> ``233240000000``
    - ``+233240000000`` -> ``233240000000``
    - ``233240000000``  -> ``233240000000``

    Returns None when the value contains no digits. Kept intentionally small
    and extensible rather than a full global phone-number parser.
    """
    if phone is None:
        return None

    digits = _NON_DIGIT.sub("", str(phone))
    if not digits:
        return None

    if len(digits) == 12 and digits.startswith("233"):
        return digits
    if len(digits) == 10 and digits.startswith("0"):
        return "233" + digits[1:]
    if len(digits) == 9:
        return "233" + digits

    return digits


def find_customer_by_phone(normalized_phone: str) -> Customer | None:
    return Customer.query.filter_by(phone=normalized_phone).first()


def get_or_create_customer(
    name: str, normalized_phone: str, email: str | None
) -> Customer:
    """Return the customer matching the normalized phone, creating it if absent."""
    existing = find_customer_by_phone(normalized_phone)
    if existing is not None:
        return existing

    customer = Customer(name=name, phone=normalized_phone, email=email)
    db.session.add(customer)
    db.session.flush()
    return customer


def list_customers(actor: User) -> list[dict]:
    """Return purchase-aggregated customer summaries for the authorized scope.

    A customer is included when they have at least one purchase in a shop the
    actor is allowed to see (all shops for SUPER_ADMIN, the assigned shop for
    SHOP_MANAGER/STAFF). Aggregation is performed in the database; only the
    per-customer aggregates are loaded into Python.
    """
    query = (
        db.session.query(
            Customer,
            func.count(Purchase.id).label("purchase_count"),
            func.max(Purchase.created_at).label("last_purchase_at"),
        )
        .join(Purchase, Purchase.customer_id == Customer.id)
        .group_by(Customer.id)
    )

    if actor.role != UserRole.SUPER_ADMIN:
        query = query.filter(Purchase.shop_id == actor.shop_id)

    rows = query.all()
    rows.sort(key=lambda r: r[2].isoformat() if r[2] else "", reverse=True)

    return [
        {
            "customer": {
                "id": customer.id,
                "name": customer.name,
                "phone": customer.phone,
                "email": customer.email,
            },
            "purchase_count": purchase_count,
            "last_purchase_at": last_purchase_at.isoformat()
            if last_purchase_at
            else None,
        }
        for customer, purchase_count, last_purchase_at in rows
    ]
