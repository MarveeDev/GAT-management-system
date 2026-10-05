from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from sqlalchemy import func
from sqlalchemy.orm import joinedload

from app.extensions import db
from app.models.customer import Customer
from app.models.product import Product, ProductStatus
from app.models.purchase import Purchase
from app.models.shop import Shop, ShopStatus
from app.models.shop_inventory import ShopInventory
from app.models.stock_movement import StockMovement, StockMovementType
from app.models.user import User, UserRole
from app.services.audit_service import AuditAction, add_audit_log
from app.services.customer_service import get_or_create_customer, normalize_phone
from app.utils.validators import clean_optional, validate_email

MAX_AMOUNT = Decimal("9999999999.99")


def _parse_amount(value):
    if value is None:
        return None, (400, "Amount is required.")
    if isinstance(value, bool):
        return None, (400, "Invalid amount.")
    try:
        dec = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None, (400, "Invalid amount.")
    if not dec.is_finite():
        return None, (400, "Invalid amount.")
    if dec < 0:
        return None, (400, "Amount must not be negative.")
    if dec > MAX_AMOUNT:
        return None, (400, "Amount is too large.")
    return dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), None


def _parse_currency(value):
    if value is None or value == "":
        return "GHS", None
    currency = str(value).strip().upper()
    if currency != "GHS":
        return None, (400, "Only GHS currency is supported.")
    return currency, None


def _parse_quantity(value):
    if value is None:
        return None, (400, "Quantity is required.")
    if isinstance(value, bool):
        return None, (400, "Invalid quantity.")
    if isinstance(value, int):
        quantity = value
    elif isinstance(value, float):
        if not value.is_integer():
            return None, (400, "Invalid quantity.")
        quantity = int(value)
    else:
        try:
            quantity = int(str(value).strip())
        except (ValueError, TypeError):
            return None, (400, "Invalid quantity.")
    if quantity <= 0:
        return None, (400, "Quantity must be greater than zero.")
    return quantity, None


def _parse_unit_price(value):
    if value is None:
        return None, (400, "unit_price is required.")
    if isinstance(value, bool):
        return None, (400, "Invalid unit_price.")
    try:
        dec = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None, (400, "Invalid unit_price.")
    if not dec.is_finite():
        return None, (400, "Invalid unit_price.")
    if dec < 0:
        return None, (400, "unit_price must not be negative.")
    if dec > MAX_AMOUNT:
        return None, (400, "unit_price is too large.")
    return dec.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), None


def _resolve_customer(data):
    if data.get("customer_id"):
        customer = db.session.get(Customer, data["customer_id"])
        if customer is None:
            return None, (404, "Customer not found.")
        return customer, None

    customer_obj = data.get("customer")
    if not isinstance(customer_obj, dict):
        return None, (400, "Customer information is required.")

    name = (customer_obj.get("name") or "").strip()
    if not name:
        return None, (400, "Customer name is required.")

    normalized = normalize_phone(customer_obj.get("phone"))
    if not normalized:
        return None, (400, "A valid phone number is required.")

    email = clean_optional(customer_obj.get("email"))
    if email and not validate_email(email):
        return None, (400, "A valid email address is required.")

    customer = get_or_create_customer(name, normalized, email)
    return customer, None


def _mask_phone(phone: str | None) -> str:
    if not phone:
        return "N/A"
    return phone[-4:]


def create_purchase(actor: User, data: dict) -> tuple[Purchase | None, tuple[int, str] | None]:
    # --- resolve shop (never trust client shop_id for shop users) ---
    if actor.role == UserRole.SUPER_ADMIN:
        shop_id = data.get("shop_id")
        if not shop_id:
            return None, (400, "shop_id is required.")
    else:
        if data.get("shop_id") and data["shop_id"] != actor.shop_id:
            return None, (403, "You do not have access to this shop.")
        shop_id = actor.shop_id

    shop = db.session.get(Shop, shop_id)
    if shop is None:
        return None, (404, "Shop not found.")
    if shop.status != ShopStatus.ACTIVE:
        return None, (400, "Cannot record a purchase for an inactive shop.")

    # --- currency ---
    currency, error = _parse_currency(data.get("currency"))
    if error:
        return None, error

    product_id = data.get("product_id")
    if not product_id:
        # The legacy path (free-text product, arbitrary amount, no inventory
        # deduction) is restricted to SUPER_ADMIN so SHOP_MANAGER/STAFF cannot
        # bypass the inventory-controlled purchase flow.
        if actor.role != UserRole.SUPER_ADMIN:
            return None, (403, "You do not have permission to perform this action.")
        return _create_legacy_purchase(actor, shop_id, data, currency)

    return _create_inventory_purchase(actor, shop_id, data, currency, product_id)


def _create_legacy_purchase(actor: User, shop_id: str, data: dict, currency: str) -> tuple[Purchase | None, tuple[int, str] | None]:
    if "quantity" in data or "unit_price" in data:
        return None, (400, "product_id is required for inventory-linked purchases.")

    # --- product ---
    product = data.get("product")
    if product is None:
        return None, (400, "Product is required.")
    product = str(product).strip()
    if not product:
        return None, (400, "Product is required.")
    if len(product) > 255:
        return None, (400, "Product is too long.")

    # --- amount ---
    amount, error = _parse_amount(data.get("amount"))
    if error:
        return None, error

    # --- customer (resolve last so failed validation leaves no orphan) ---
    customer, error = _resolve_customer(data)
    if error:
        return None, error

    purchase = Purchase(
        shop_id=shop_id,
        staff_id=actor.id,
        customer_id=customer.id,
        product=product,
        amount=amount,
        currency=currency,
    )
    db.session.add(purchase)
    db.session.flush()

    add_audit_log(
        actor.id,
        shop_id,
        AuditAction.PURCHASE_CREATED,
        "PURCHASE",
        purchase.id,
        f"Purchase created for customer ending {_mask_phone(customer.phone)}.",
    )

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return purchase, None


def _create_inventory_purchase(actor: User, shop_id: str, data: dict, currency: str, product_id: str) -> tuple[Purchase | None, tuple[int, str] | None]:
    # --- product ---
    product = db.session.get(Product, product_id)
    if product is None:
        return None, (404, "Product not found.")
    if product.status != ProductStatus.ACTIVE:
        return None, (400, "This product is not active.")

    # --- quantity ---
    quantity, error = _parse_quantity(data.get("quantity"))
    if error:
        return None, error

    # --- unit price (and range validation) ---
    unit_price, error = _parse_unit_price(data.get("unit_price"))
    if error:
        return None, error
    if unit_price < product.minimum_price or unit_price > product.maximum_price:
        return None, (
            400,
            f"unit_price must be between {product.minimum_price} and {product.maximum_price}.",
        )

    # --- lock and check stock (atomic with deduction below) ---
    inventory = (
        ShopInventory.query.filter_by(product_id=product.id, shop_id=shop_id)
        .with_for_update()
        .first()
    )
    available = inventory.quantity if inventory else 0
    if available < quantity:
        return None, (
            400,
            f"Insufficient stock for {product.name}. Available: {available}, requested: {quantity}.",
        )

    new_quantity = available - quantity

    # --- customer (resolve last so failed validation leaves no orphan) ---
    customer, error = _resolve_customer(data)
    if error:
        return None, error

    amount = (unit_price * quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    purchase = Purchase(
        shop_id=shop_id,
        staff_id=actor.id,
        customer_id=customer.id,
        product=product.name,
        product_id=product.id,
        quantity=quantity,
        unit_price=unit_price,
        amount=amount,
        currency=currency,
    )

    if inventory is None:
        inventory = ShopInventory(
            product_id=product.id, shop_id=shop_id, quantity=new_quantity
        )
        db.session.add(inventory)
    else:
        inventory.quantity = new_quantity

    db.session.add(purchase)
    db.session.flush()

    movement = StockMovement(
        product_id=product.id,
        shop_id=shop_id,
        quantity_change=-quantity,
        quantity_before=available,
        quantity_after=new_quantity,
        movement_type=StockMovementType.SALE,
        reference_id=purchase.id,
        actor_id=actor.id,
    )
    db.session.add(movement)

    add_audit_log(
        actor.id,
        shop_id,
        AuditAction.PURCHASE_CREATED,
        "PURCHASE",
        purchase.id,
        f"Purchase created for customer ending {_mask_phone(customer.phone)}.",
    )

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    purchase.remaining_stock = new_quantity
    return purchase, None


def get_purchase(actor: User, purchase_id: str) -> tuple[Purchase | None, tuple[int, str] | None]:
    purchase = db.session.get(Purchase, purchase_id)
    if purchase is None:
        return None, (404, "Purchase not found.")
    if actor.role != UserRole.SUPER_ADMIN and purchase.shop_id != actor.shop_id:
        return None, (403, "You do not have access to this purchase.")
    return purchase, None


def list_purchases(
    actor: User,
    *,
    shop_id: str | None = None,
    staff_id: str | None = None,
    customer_id: str | None = None,
    date_from=None,
    date_to=None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 20,
) -> tuple[list[Purchase], dict, dict]:
    page = max(1, page)
    per_page = min(max(1, per_page), 100)

    query = Purchase.query.options(
        joinedload(Purchase.customer), joinedload(Purchase.staff),
        joinedload(Purchase.product_ref),
    )

    if actor.role == UserRole.SUPER_ADMIN:
        if shop_id:
            query = query.filter(Purchase.shop_id == shop_id)
    else:
        query = query.filter(Purchase.shop_id == actor.shop_id)

    if staff_id:
        query = query.filter(Purchase.staff_id == staff_id)
    if customer_id:
        query = query.filter(Purchase.customer_id == customer_id)
    if date_from:
        query = query.filter(Purchase.created_at >= date_from)
    if date_to:
        query = query.filter(Purchase.created_at <= date_to)
    if search:
        query = query.filter(Purchase.product.ilike(f"%{search}%"))

    total = query.count()
    unique_customers = query.with_entities(
        func.count(func.distinct(Purchase.customer_id))
    ).scalar()
    pages = (total + per_page - 1) // per_page

    purchases = (
        query.order_by(Purchase.created_at.desc(), Purchase.id.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    pagination = {"page": page, "per_page": per_page, "total": total, "pages": pages}
    summary = {"unique_customers": unique_customers}
    return purchases, pagination, summary
