from sqlalchemy import CheckConstraint, Index

from app.extensions import db
from app.models.base import BaseModel


class Purchase(BaseModel):
    __tablename__ = "purchases"
    __table_args__ = (
        CheckConstraint("amount >= 0", name="ck_purchases_amount_nonnegative"),
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
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default="GHS")

    shop = db.relationship("Shop", back_populates="purchases")
    staff = db.relationship("User", back_populates="purchases")
    customer = db.relationship("Customer", back_populates="purchases")
    sms_logs = db.relationship("SMSLog", back_populates="purchase")

    def __repr__(self) -> str:
        return f"<Purchase {self.product} {self.amount} {self.currency}>"
