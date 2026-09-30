import re

from app.extensions import db
from app.models.customer import Customer

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
