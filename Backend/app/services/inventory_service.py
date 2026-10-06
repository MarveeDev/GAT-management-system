from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.product import Product, ProductStatus
from app.models.shop import Shop
from app.models.shop_inventory import ShopInventory
from app.models.stock_movement import StockMovement, StockMovementType
from app.models.user import User, UserRole
from app.services.audit_service import AuditAction, add_audit_log


def _parse_quantity(value):
    if value is None:
        return None, (400, "Quantity is required.")
    if isinstance(value, bool):
        return None, (400, "Invalid quantity.")
    try:
        quantity = int(value)
    except (ValueError, TypeError):
        return None, (400, "Invalid quantity.")
    if quantity < 0:
        return None, (400, "Quantity must not be negative.")
    return quantity, None


def _resolve_shop_access(actor: User, shop_id: str | None) -> tuple[str | None, tuple[int, str] | None]:
    """Return the effective shop_id the actor may view, or an error."""
    if actor.role == UserRole.SUPER_ADMIN:
        return shop_id, None
    if shop_id is not None and shop_id != actor.shop_id:
        return None, (403, "You do not have access to this shop.")
    return actor.shop_id, None


def list_inventory(
    actor: User,
    shop_id: str | None = None,
    product_id: str | None = None,
) -> tuple[list[ShopInventory] | None, tuple[int, str] | None]:
    effective_shop_id, error = _resolve_shop_access(actor, shop_id)
    if error:
        return None, error

    query = ShopInventory.query.options(
        joinedload(ShopInventory.product), joinedload(ShopInventory.shop)
    )
    if actor.role != UserRole.SUPER_ADMIN:
        query = query.join(ShopInventory.product).filter(
            Product.status == ProductStatus.ACTIVE
        )
    if effective_shop_id:
        query = query.filter(ShopInventory.shop_id == effective_shop_id)
    if product_id:
        query = query.filter(ShopInventory.product_id == product_id)

    inventories = query.order_by(ShopInventory.product_id, ShopInventory.shop_id).all()
    return inventories, None


def get_product_inventory(
    actor: User, product_id: str
) -> tuple[list[ShopInventory] | None, tuple[int, str] | None]:
    product = db.session.get(Product, product_id)
    if product is None:
        return None, (404, "Product not found.")
    if actor.role != UserRole.SUPER_ADMIN and product.status != ProductStatus.ACTIVE:
        return None, (404, "Product not found.")

    effective_shop_id, error = _resolve_shop_access(actor, None)
    if error:
        return None, error

    query = ShopInventory.query.options(
        joinedload(ShopInventory.product), joinedload(ShopInventory.shop)
    ).filter(ShopInventory.product_id == product_id)
    if effective_shop_id:
        query = query.filter(ShopInventory.shop_id == effective_shop_id)

    inventories = query.order_by(ShopInventory.shop_id).all()
    return inventories, None


def set_stock(
    actor: User,
    product_id: str,
    shop_id: str,
    quantity: int,
) -> tuple[ShopInventory | None, tuple[int, str] | None]:
    if actor.role != UserRole.SUPER_ADMIN:
        return None, (403, "You do not have permission to modify stock.")

    quantity, error = _parse_quantity(quantity)
    if error:
        return None, error

    product = db.session.get(Product, product_id)
    if product is None:
        return None, (404, "Product not found.")
    shop = db.session.get(Shop, shop_id)
    if shop is None:
        return None, (404, "Shop not found.")

    inventory = ShopInventory.query.filter_by(
        product_id=product_id, shop_id=shop_id
    ).first()

    if inventory is None:
        inventory = ShopInventory(
            product_id=product_id, shop_id=shop_id, quantity=quantity
        )
        db.session.add(inventory)
        db.session.flush()

        movement = StockMovement(
            product_id=product_id,
            shop_id=shop_id,
            quantity_change=quantity,
            quantity_before=0,
            quantity_after=quantity,
            movement_type=StockMovementType.INITIAL_STOCK,
            actor_id=actor.id,
        )
        db.session.add(movement)

        add_audit_log(
            actor.id,
            shop_id,
            AuditAction.STOCK_INITIALIZED,
            "INVENTORY",
            inventory.id,
            f"Initial stock set to {quantity} for product '{product.name}'.",
        )
    else:
        old_quantity = inventory.quantity
        change = quantity - old_quantity
        inventory.quantity = quantity

        movement = StockMovement(
            product_id=product_id,
            shop_id=shop_id,
            quantity_change=change,
            quantity_before=old_quantity,
            quantity_after=quantity,
            movement_type=StockMovementType.MANUAL_ADJUSTMENT,
            actor_id=actor.id,
        )
        db.session.add(movement)

        add_audit_log(
            actor.id,
            shop_id,
            AuditAction.STOCK_ADJUSTED,
            "INVENTORY",
            inventory.id,
            f"Stock adjusted from {old_quantity} to {quantity} for product '{product.name}'.",
        )

    db.session.commit()
    return inventory, None


def list_movements(
    actor: User,
    product_id: str,
    shop_id: str | None = None,
) -> tuple[list[StockMovement] | None, tuple[int, str] | None]:
    if actor.role != UserRole.SUPER_ADMIN:
        return None, (403, "You do not have permission to view stock movement history.")

    query = StockMovement.query.filter(StockMovement.product_id == product_id)
    if shop_id:
        query = query.filter(StockMovement.shop_id == shop_id)

    movements = query.order_by(StockMovement.created_at.desc(), StockMovement.id.desc()).all()
    return movements, None
