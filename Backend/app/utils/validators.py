import re

from app.models.user import UserRole

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MIN_PASSWORD_LENGTH = 8


def validate_email(email: str) -> bool:
    return bool(email) and EMAIL_RE.match(email) is not None


def validate_password(password: str) -> bool:
    return bool(password) and len(password) >= MIN_PASSWORD_LENGTH


def validate_shop_assignment(role: str, shop_id: str | None) -> str | None:
    """Return an error message if the role/shop assignment is invalid.

    SUPER_ADMIN may have no shop. SHOP_MANAGER and STAFF must be assigned to
    exactly one shop. Returns None when the assignment is valid.
    """
    if role == UserRole.SUPER_ADMIN:
        return None
    if role in (UserRole.SHOP_MANAGER, UserRole.STAFF):
        if shop_id is None or shop_id == "":
            return "A shop assignment is required for this role."
        return None
    return f"Unknown role: {role}"
