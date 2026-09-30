from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models.shop import Shop, ShopStatus
from app.models.user import User, UserRole, UserStatus
from app.services.audit_service import AuditAction, add_audit_log
from app.utils.validators import clean_optional, validate_email, validate_password


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
    phone = clean_optional(phone)

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


def get_user(user_id: str) -> User | None:
    return db.session.get(User, user_id)


def list_users(
    actor: User,
    shop_id: str | None = None,
    role: str | None = None,
    status: str | None = None,
) -> list[User]:
    query = User.query
    if actor.role == UserRole.SUPER_ADMIN:
        if shop_id:
            query = query.filter(User.shop_id == shop_id)
    else:
        query = query.filter(User.shop_id == actor.shop_id)

    if role:
        query = query.filter(User.role == role)
    if status:
        query = query.filter(User.status == status)

    return query.order_by(User.created_at).all()


def get_visible_user(actor: User, user_id: str) -> tuple[User | None, tuple[int, str] | None]:
    target = db.session.get(User, user_id)
    if target is None:
        return None, (404, "User not found.")

    if actor.role == UserRole.SUPER_ADMIN:
        return target, None

    if actor.role == UserRole.STAFF:
        if target.id == actor.id:
            return target, None
        return None, (403, "You do not have access to this user.")

    if target.shop_id != actor.shop_id:
        return None, (403, "You do not have access to this user.")

    return target, None


def create_user(actor: User, data: dict) -> tuple[User | None, tuple[int, str] | None]:
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    phone = clean_optional(data.get("phone"))
    password = data.get("password") or ""
    role = data.get("role")
    shop_id = data.get("shop_id")

    if not name:
        return None, (400, "Full name is required.")
    if not validate_email(email):
        return None, (400, "A valid email address is required.")
    if not validate_password(password):
        return None, (400, "Password must be at least 8 characters.")
    if role not in (UserRole.SHOP_MANAGER, UserRole.STAFF):
        return None, (400, "Role must be SHOP_MANAGER or STAFF.")
    if not shop_id:
        return None, (400, "A shop assignment is required.")

    # Authorization: who may create which users.
    if actor.role == UserRole.SHOP_MANAGER:
        if role != UserRole.STAFF:
            return None, (403, "You can only create STAFF accounts.")
        if shop_id != actor.shop_id:
            return None, (403, "You can only create staff for your own shop.")
    elif actor.role != UserRole.SUPER_ADMIN:
        return None, (403, "You do not have permission to create users.")

    shop = db.session.get(Shop, shop_id)
    if shop is None:
        return None, (404, "Shop not found.")
    if shop.status != ShopStatus.ACTIVE:
        return None, (400, "Cannot assign a user to an inactive shop.")

    if User.query.filter_by(email=email).first() is not None:
        return None, (409, "A user with this email already exists.")

    user = User(
        name=name,
        email=email,
        phone=phone,
        password_hash=generate_password_hash(password),
        role=role,
        shop_id=shop_id,
        status=UserStatus.ACTIVE,
    )
    db.session.add(user)
    db.session.flush()

    add_audit_log(
        actor.id,
        shop_id,
        AuditAction.USER_CREATED,
        "USER",
        user.id,
        f"User '{user.name}' ({user.email}) created as {role}.",
    )
    db.session.commit()
    return user, None


def update_user(actor: User, target: User, data: dict) -> tuple[User | None, tuple[int, str] | None]:
    # Authorization.
    if actor.role == UserRole.SUPER_ADMIN:
        pass
    elif actor.role == UserRole.SHOP_MANAGER:
        if target.role != UserRole.STAFF:
            return None, (403, "You can only manage staff in your shop.")
        if target.shop_id != actor.shop_id:
            return None, (403, "You cannot modify users outside your shop.")
        if "role" in data and data.get("role") != UserRole.STAFF:
            return None, (403, "You cannot change a staff member's role.")
    else:
        return None, (403, "You do not have permission to update users.")

    new_role = data.get("role", target.role)
    new_shop_id = data.get("shop_id", target.shop_id)
    new_status = data.get("status", target.status)

    # Validate proposed values.
    if "name" in data and not (data["name"] or "").strip():
        return None, (400, "Full name is required.")
    if "role" in data:
        if new_role not in UserRole.VALUES:
            return None, (400, "Invalid role.")
        if new_role == UserRole.SUPER_ADMIN:
            return None, (403, "Cannot set role to SUPER_ADMIN.")
    if "status" in data and new_status not in UserStatus.VALUES:
        return None, (400, "Invalid status.")

    # Validate the final shop assignment.
    if new_role in (UserRole.SHOP_MANAGER, UserRole.STAFF):
        if not new_shop_id:
            return None, (400, "A shop assignment is required for this role.")
        if "shop_id" in data:
            shop = db.session.get(Shop, new_shop_id)
            if shop is None:
                return None, (404, "Shop not found.")
            if shop.status != ShopStatus.ACTIVE:
                return None, (400, "Cannot assign a user to an inactive shop.")

    # A shop manager must not move staff to another shop.
    if (
        actor.role == UserRole.SHOP_MANAGER
        and "shop_id" in data
        and new_shop_id != actor.shop_id
    ):
        return None, (403, "You cannot move staff to another shop.")

    old_name = target.name
    old_role = target.role
    old_shop_id = target.shop_id
    old_status = target.status

    if "name" in data:
        target.name = (data["name"] or "").strip()
    if "phone" in data:
        target.phone = clean_optional(data["phone"])
    if "role" in data:
        target.role = new_role
    if "shop_id" in data:
        target.shop_id = new_shop_id or None
    if "status" in data:
        target.status = new_status

    if "role" in data and new_role != old_role:
        add_audit_log(
            actor.id,
            target.shop_id,
            AuditAction.USER_ROLE_CHANGED,
            "USER",
            target.id,
            f"Role changed from {old_role} to {new_role}.",
        )
    if "shop_id" in data and (new_shop_id or None) != old_shop_id:
        add_audit_log(
            actor.id,
            target.shop_id,
            AuditAction.USER_SHOP_CHANGED,
            "USER",
            target.id,
            f"Shop assignment changed.",
        )
    if "status" in data and new_status != old_status:
        action = (
            AuditAction.USER_ACTIVATED
            if new_status == UserStatus.ACTIVE
            else AuditAction.USER_DEACTIVATED
        )
        add_audit_log(
            actor.id,
            target.shop_id,
            action,
            "USER",
            target.id,
            f"User {'activated' if new_status == UserStatus.ACTIVE else 'deactivated'}.",
        )
    if ("name" in data and target.name != old_name) or ("phone" in data):
        add_audit_log(
            actor.id,
            target.shop_id,
            AuditAction.USER_UPDATED,
            "USER",
            target.id,
            "User profile updated.",
        )

    db.session.commit()
    return target, None


def update_password(actor: User, target: User, password: str) -> tuple[User | None, tuple[int, str] | None]:
    if not validate_password(password):
        return None, (400, "Password must be at least 8 characters.")

    if actor.role == UserRole.SUPER_ADMIN:
        pass
    elif actor.role == UserRole.SHOP_MANAGER:
        if target.role != UserRole.STAFF or target.shop_id != actor.shop_id:
            return None, (403, "You can only reset passwords for staff in your own shop.")
    else:
        return None, (403, "You do not have permission to reset passwords.")

    target.password_hash = generate_password_hash(password)
    add_audit_log(
        actor.id,
        target.shop_id,
        AuditAction.USER_PASSWORD_RESET,
        "USER",
        target.id,
        f"Password reset for user '{target.email}'.",
    )
    db.session.commit()
    return target, None
