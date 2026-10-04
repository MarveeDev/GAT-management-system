from sqlalchemy import CheckConstraint

from app.extensions import db
from app.models.base import BaseModel


class ProductStatus:
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

    VALUES = (ACTIVE, INACTIVE)


class Product(BaseModel):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("length(name) > 0", name="ck_products_name_not_empty"),
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')", name="ck_products_status"
        ),
        CheckConstraint(
            "minimum_price >= 0", name="ck_products_minimum_price_nonnegative"
        ),
        CheckConstraint(
            "maximum_price >= 0", name="ck_products_maximum_price_nonnegative"
        ),
        CheckConstraint(
            "minimum_price <= maximum_price", name="ck_products_price_range"
        ),
    )

    name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(150), nullable=True)
    minimum_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    maximum_price = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default=ProductStatus.ACTIVE)

    inventories = db.relationship("ShopInventory", back_populates="product")
    movements = db.relationship("StockMovement", back_populates="product")
    purchases = db.relationship("Purchase", back_populates="product_ref")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "minimum_price": str(self.minimum_price) if self.minimum_price is not None else None,
            "maximum_price": str(self.maximum_price) if self.maximum_price is not None else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<Product {self.name}>"
