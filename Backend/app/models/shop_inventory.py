from sqlalchemy import CheckConstraint, UniqueConstraint

from app.extensions import db
from app.models.base import BaseModel


class ShopInventory(BaseModel):
    __tablename__ = "shop_inventories"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_shop_inventories_quantity_nonnegative"),
        UniqueConstraint("product_id", "shop_id", name="uq_shop_inventories_product_shop"),
    )

    shop_id = db.Column(
        db.String(36), db.ForeignKey("shops.id"), nullable=False, index=True
    )
    product_id = db.Column(
        db.String(36), db.ForeignKey("products.id"), nullable=False, index=True
    )
    quantity = db.Column(db.Integer, nullable=False, default=0)

    shop = db.relationship("Shop", back_populates="inventories")
    product = db.relationship("Product", back_populates="inventories")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "shop_id": self.shop_id,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "product": self.product.to_dict() if self.product else None,
            "shop": {"id": self.shop.id, "name": self.shop.name} if self.shop else None,
        }

    def __repr__(self) -> str:
        return f"<ShopInventory product={self.product_id} shop={self.shop_id} qty={self.quantity}>"
