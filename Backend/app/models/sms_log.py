from sqlalchemy import CheckConstraint, Index

from app.extensions import db
from app.models.base import BaseModel


class SMSStatus:
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"

    VALUES = (PENDING, SENT, FAILED)


class SMSLog(BaseModel):
    __tablename__ = "sms_logs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'SENT', 'FAILED')", name="ck_sms_logs_status"
        ),
        Index("ix_sms_logs_created_at", "created_at"),
    )

    shop_id = db.Column(
        db.String(36), db.ForeignKey("shops.id"), nullable=False, index=True
    )
    purchase_id = db.Column(
        db.String(36), db.ForeignKey("purchases.id"), nullable=False, index=True
    )
    customer_id = db.Column(
        db.String(36), db.ForeignKey("customers.id"), nullable=False, index=True
    )
    phone_number = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    provider = db.Column(db.String(50), nullable=True)
    provider_message_id = db.Column(db.String(255), nullable=True)
    status = db.Column(
        db.String(20), nullable=False, default=SMSStatus.PENDING, index=True
    )
    error_message = db.Column(db.Text, nullable=True)
    sent_at = db.Column(db.DateTime(timezone=True), nullable=True)

    shop = db.relationship("Shop", back_populates="sms_logs")
    purchase = db.relationship("Purchase", back_populates="sms_logs")
    customer = db.relationship("Customer", back_populates="sms_logs")

    def __repr__(self) -> str:
        return f"<SMSLog {self.status} to {self.phone_number}>"
