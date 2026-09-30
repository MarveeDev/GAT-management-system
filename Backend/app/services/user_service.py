from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models.user import User, UserRole, UserStatus
from app.utils.validators import validate_email, validate_password


def create_super_admin(
    name: str, email: str, phone: str | None, password: str
) -> tuple[User | None, str | None]:
    """Create a SUPER_ADMIN account, returning (user, error_message).

    The caller (CLI or future admin UI) must already have confirmed the
    password. Validation is performed here so the same rules apply
    everywhere an administrator is created.
    """
    name = (name or "").strip()
    email = (email or "").strip().lower()
    phone = (phone or "").strip() or None

    if not name:
        return None, "Full name is required."
    if not validate_email(email):
        return None, "A valid email address is required."
    if not validate_password(password):
        return None, "Password must be at least 8 characters."
    if User.query.filter_by(email=email).first() is not None:
        return None, "A user with this email already exists."

    user = User(
        name=name,
        email=email,
        phone=phone,
        password_hash=generate_password_hash(password),
        role=UserRole.SUPER_ADMIN,
        shop_id=None,
        status=UserStatus.ACTIVE,
    )
    db.session.add(user)
    db.session.commit()

    return user, None
