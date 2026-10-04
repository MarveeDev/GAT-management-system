from sqlalchemy import CheckConstraint, Index

from app.extensions import db
from app.models.base import gen_uuid, utcnow


class StockMovementType:
    INITIAL_STOCK = "INITIAL_STOCK"
    MANUAL_ADJUSTMENT = "MANUAL_ADJUSTMENT"
    SALE = "SALE"

    VALUES = (INITIAL_STOCK, MANUAL_ADJUSTMENT, SALE)


class StockMovement(db.Model):
    __tablename__ = "stock_movements"
    __table_args__ = (
        CheckConstraint(
            "movement_type IN ('INITIAL_STOCK', 'MANUAL_ADJUSTMENT', 'SALE')",
            name="ck_stock_movements_movement_type",
        ),
        Index("ix_stock_movements_product_shop_created", "product_id", "shop_id", "created_at"),
    )

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    product_id = db.Column(
        db.String(36), db.ForeignKey("products.id"), nullable=False, index=True
    )
    shop_id = db.Column(
        db.String(36), db.ForeignKey("shops.id"), nullable=False, index=True
    )
    quantity_change = db.Column(db.Integer, nullable=False)
    quantity_before = db.Column(db.Integer, nullable=False)
    quantity_after = db.Column(db.Integer, nullable=False)
    movement_type = db.Column(db.String(30), nullable=False)
    reference_id = db.Column(db.String(36), nullable=True)
    actor_id = db.Column(
        db.String(36), db.ForeignKey("users.id"), nullable=True, index=True
    )
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    product = db.relationship("Product", back_populates="movements")
    shop = db.relationship("Shop", back_populates="stock_movements")
    actor = db.relationship("User", back_populates="stock_movements")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "shop_id": self.shop_id,
            "quantity_change": self.quantity_change,
            "quantity_before": self.quantity_before,
            "quantity_after": self.quantity_after,
            "movement_type": self.movement_type,
            "reference_id": self.reference_id,
            "actor_id": self.actor_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<StockMovement {self.movement_type} product={self.product_id} change={self.quantity_change}>"
