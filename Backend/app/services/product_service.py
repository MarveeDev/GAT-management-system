from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from app.extensions import db
from app.models.product import Product, ProductStatus
from app.models.user import User, UserRole
from app.services.audit_service import AuditAction, add_audit_log
from app.utils.validators import clean_optional

MAX_PRICE = Decimal("9999999999.99")


def _parse_price(value, field_name):
    if value is None:
        return None, (400, f"{field_name} is required.")
    if isinstance(value, bool):
        return None, (400, f"Invalid {field_name}.")
    try:
        dec = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None, (400, f"Invalid {field_name}.")
    if not dec.is_finite():
        return None, (400, f"Invalid {field_name}.")
    if dec < 0:
        return None, (400, f"{field_name} must not be negative.")
    if dec > MAX_PRICE:
        return None, (400, f"{field_name} is too large.")
    return dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), None


def _normalize_name(name) -> str:
    return (name or "").strip().casefold()


def _active_name_conflict(product_id: str | None, name: str) -> bool:
    normalized = _normalize_name(name)
    query = Product.query.filter(Product.status == ProductStatus.ACTIVE)
    if product_id is not None:
        query = query.filter(Product.id != product_id)
    for candidate in query.all():
        if _normalize_name(candidate.name) == normalized:
            return True
    return False


def list_products(actor: User, search: str | None = None, status: str | None = None) -> list[Product]:
    query = Product.query

    if actor.role != UserRole.SUPER_ADMIN:
        query = query.filter(Product.status == ProductStatus.ACTIVE)
    elif status:
        query = query.filter(Product.status == status)

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(Product.name.ilike(term))

    return query.order_by(Product.name).all()


def get_product(product_id: str) -> Product | None:
    return db.session.get(Product, product_id)


def get_visible_product(actor: User, product_id: str) -> tuple[Product | None, tuple[int, str] | None]:
    product = db.session.get(Product, product_id)
    if product is None:
        return None, (404, "Product not found.")
    if actor.role != UserRole.SUPER_ADMIN and product.status != ProductStatus.ACTIVE:
        return None, (404, "Product not found.")
    return product, None


def create_product(actor: User, data: dict) -> tuple[Product | None, tuple[int, str] | None]:
    name = (data.get("name") or "").strip()
    if not name:
        return None, (400, "Product name is required.")
    if len(name) > 255:
        return None, (400, "Product name is too long.")

    category = clean_optional(data.get("category"))

    minimum_price, error = _parse_price(data.get("minimum_price"), "minimum_price")
    if error:
        return None, error
    maximum_price, error = _parse_price(data.get("maximum_price"), "maximum_price")
    if error:
        return None, error
    if minimum_price > maximum_price:
        return None, (400, "minimum_price must not exceed maximum_price.")

    status = data.get("status") or ProductStatus.ACTIVE
    if status not in ProductStatus.VALUES:
        return None, (400, "Invalid product status.")

    if _active_name_conflict(None, name):
        return None, (409, "An active product with this name already exists.")

    product = Product(
        name=name,
        category=category,
        minimum_price=minimum_price,
        maximum_price=maximum_price,
        status=status,
    )
    db.session.add(product)
    db.session.flush()

    add_audit_log(
        actor.id,
        None,
        AuditAction.PRODUCT_CREATED,
        "PRODUCT",
        product.id,
        f"Product '{product.name}' created.",
    )
    db.session.commit()
    return product, None


def update_product(actor: User, product: Product, data: dict) -> tuple[Product | None, tuple[int, str] | None]:
    if "name" in data:
        name = (data["name"] or "").strip()
        if not name:
            return None, (400, "Product name is required.")
        if len(name) > 255:
            return None, (400, "Product name is too long.")
    else:
        name = product.name

    new_status = data.get("status", product.status)
    if "status" in data and new_status not in ProductStatus.VALUES:
        return None, (400, "Invalid product status.")

    minimum_price = product.minimum_price
    maximum_price = product.maximum_price
    if "minimum_price" in data:
        minimum_price, error = _parse_price(data["minimum_price"], "minimum_price")
        if error:
            return None, error
    if "maximum_price" in data:
        maximum_price, error = _parse_price(data["maximum_price"], "maximum_price")
        if error:
            return None, error
    if minimum_price > maximum_price:
        return None, (400, "minimum_price must not exceed maximum_price.")

    will_be_active = new_status == ProductStatus.ACTIVE
    name_changed = name.strip() != product.name
    if will_be_active and (name_changed or product.status != ProductStatus.ACTIVE):
        if _active_name_conflict(product.id, name):
            return None, (409, "An active product with this name already exists.")

    old_status = product.status
    product.name = name
    if "category" in data:
        product.category = clean_optional(data["category"])
    product.minimum_price = minimum_price
    product.maximum_price = maximum_price
    product.status = new_status

    if "status" in data and new_status != old_status:
        action = (
            AuditAction.PRODUCT_ACTIVATED
            if new_status == ProductStatus.ACTIVE
            else AuditAction.PRODUCT_DEACTIVATED
        )
        description = f"Product '{product.name}' {'activated' if new_status == ProductStatus.ACTIVE else 'deactivated'}."
    else:
        action = AuditAction.PRODUCT_UPDATED
        description = f"Product '{product.name}' updated."

    add_audit_log(actor.id, None, action, "PRODUCT", product.id, description)
    db.session.commit()
    return product, None
