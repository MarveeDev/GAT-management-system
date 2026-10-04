from sqlalchemy import CheckConstraint, Index

from app.extensions import db
from app.models.base import BaseModel


class Purchase(BaseModel):
    __tablename__ = "purchases"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_purchases_amount_nonnegative"),
        CheckConstraint(
            "quantity IS NULL OR quantity > 0", name="ck_purchases_quantity_positive"
        ),
        CheckConstraint(
            "unit_price IS NULL OR unit_price >= 0",
            name="ck_purchases_unit_price_nonnegative",
        ),
        Index("ix_purchases_created_at", "created_at"),
    )

    shop_id = db.Column(
        db.String(36), db.ForeignKey("shops.id"), nullable=False, index=True
    )
    staff_id = db.Column(
        db.String(36), db.ForeignKey("users.id"), nullable=False, index=True
    )
    customer_id = db.Column(
        db.String(36), db.ForeignKey("customers.id"), nullable=False, index=True
    )
    product = db.Column(db.String(255), nullable=False)
    product_id = db.Column(
        db.String(36), db.ForeignKey("products.id"), nullable=True, index=True
    )
    quantity = db.Column(db.Integer, nullable=True)
    unit_price = db.Column(db.Numeric(12, 2), nullable=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="GHS")

    shop = db.relationship("Shop", back_populates="purchases")
    staff = db.relationship("User", back_populates="purchases")
    customer = db.relationship("Customer", back_populates="purchases")
    sms_logs = db.relationship("SMSLog", back_populates="purchase")
    product_ref = db.relationship("Product", back_populates="purchases")

    def to_dict(self) -> dict:
        result = {
            "id": self.id,
            "shop_id": self.shop_id,
            "staff_id": self.staff_id,
            "customer_id": self.customer_id,
            "product": self.product,
            "product_id": self.product_id,
            "quantity": self.quantity,
            "unit_price": str(self.unit_price) if self.unit_price is not None else None,
            "amount": str(self.amount) if self.amount is not None else None,
            "currency": self.currency,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "customer": self.customer.to_dict() if self.customer else None,
            "staff": self._staff_dict() if self.staff else None,
            "product_info": self._product_info_dict() if self.product_ref else None,
        }
        remaining_stock = getattr(self, "remaining_stock", None)
        if remaining_stock is not None:
            result["remaining_stock"] = remaining_stock
        return result

    def _product_info_dict(self) -> dict:
        return {
            "id": self.product_ref.id,
            "name": self.product_ref.name,
            "category": self.product_ref.category,
        }

    def _staff_dict(self) -> dict:
        return {
            "id": self.staff.id,
            "name": self.staff.name,
            "email": self.staff.email,
            "role": self.staff.role,
        }

    def __repr__(self) -> str:
        return f"<Purchase {self.product} {self.amount} {self.currency}>"
