from app.extensions import db
from app.models.audit_log import AuditLog


class AuditAction:
    SHOP_CREATED = "shop.created"
    SHOP_UPDATED = "shop.updated"
    SHOP_ACTIVATED = "shop.activated"
    SHOP_DEACTIVATED = "shop.deactivated"

    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_ACTIVATED = "user.activated"
    USER_DEACTIVATED = "user.deactivated"
    USER_ROLE_CHANGED = "user.role_changed"
    USER_SHOP_CHANGED = "user.shop_changed"
    USER_PASSWORD_RESET = "user.password_reset"

    PURCHASE_CREATED = "purchase.created"


def add_audit_log(
    user_id: str | None,
    shop_id: str | None,
    action: str,
    entity_type: str,
    entity_id: str | None,
    description: str | None,
) -> None:
    """Stage an AuditLog row in the current session.

    The caller is responsible for committing the surrounding transaction so
    the audit record is persisted atomically with the business action.
    """
    db.session.add(
        AuditLog(
            user_id=user_id,
            shop_id=shop_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
        )
    )
