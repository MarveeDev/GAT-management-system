from app.extensions import db
from app.models.shop import Shop, ShopStatus
from app.models.user import User, UserRole
from app.services.audit_service import AuditAction, add_audit_log
from app.utils.validators import clean_optional


def list_shops_for_actor(actor: User) -> list[Shop]:
    if actor.role == UserRole.SUPER_ADMIN:
        return Shop.query.order_by(Shop.created_at).all()
    shop = db.session.get(Shop, actor.shop_id)
    return [shop] if shop else []


def get_shop(shop_id: str) -> Shop | None:
    return db.session.get(Shop, shop_id)


def create_shop(actor: User, data: dict) -> tuple[Shop | None, tuple[int, str] | None]:
    name = (data.get("name") or "").strip()
    if not name:
        return None, (400, "Shop name is required.")

    status = data.get("status") or ShopStatus.ACTIVE
    if status not in ShopStatus.VALUES:
        return None, (400, "Invalid shop status.")

    shop = Shop(
        name=name,
        location=clean_optional(data.get("location")),
        phone=clean_optional(data.get("phone")),
        sender_id=clean_optional(data.get("sender_id")),
        status=status,
    )
    db.session.add(shop)
    db.session.flush()

    add_audit_log(
        actor.id,
        shop.id,
        AuditAction.SHOP_CREATED,
        "SHOP",
        shop.id,
        f"Shop '{shop.name}' created.",
    )
    db.session.commit()
    return shop, None


def update_shop(actor: User, shop: Shop, data: dict) -> tuple[Shop | None, tuple[int, str] | None]:
    if "name" in data:
        name = (data["name"] or "").strip()
        if not name:
            return None, (400, "Shop name is required.")
        shop.name = name

    if "location" in data:
        shop.location = clean_optional(data["location"])
    if "phone" in data:
        shop.phone = clean_optional(data["phone"])
    if "sender_id" in data:
        shop.sender_id = clean_optional(data["sender_id"])

    status_changed = False
    if "status" in data:
        status = data["status"]
        if status not in ShopStatus.VALUES:
            return None, (400, "Invalid shop status.")
        if status != shop.status:
            shop.status = status
            status_changed = True

    if status_changed:
        action = (
            AuditAction.SHOP_ACTIVATED
            if shop.status == ShopStatus.ACTIVE
            else AuditAction.SHOP_DEACTIVATED
        )
        description = f"Shop '{shop.name}' {'activated' if shop.status == ShopStatus.ACTIVE else 'deactivated'}."
    else:
        action = AuditAction.SHOP_UPDATED
        description = f"Shop '{shop.name}' updated."

    add_audit_log(actor.id, shop.id, action, "SHOP", shop.id, description)
    db.session.commit()
    return shop, None
