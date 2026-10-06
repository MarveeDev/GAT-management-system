from sqlalchemy import CheckConstraint, Index

from app.extensions import db
from app.models.base import BaseModel


class SMSStatus:
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"
    # Ambiguous provider outcome (see SMS recovery): the message may or may
    # not have been delivered, and must NOT be automatically retried.
    REVIEW = "REVIEW"

    VALUES = (PENDING, SENT, FAILED, REVIEW)


class SMSLog(BaseModel):
    __tablename__ = "sms_logs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING', 'SENT', 'FAILED', 'REVIEW')",
            name="ck_sms_logs_status",
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

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "shop_id": self.shop_id,
            "purchase_id": self.purchase_id,
            "customer_id": self.customer_id,
            "phone_number": self.phone_number,
            "message": self.message,
            "provider": self.provider,
            "provider_message_id": self.provider_message_id,
            "status": self.status,
            "error_message": self.error_message,
            "sent_at": self.sent_at.isoformat() if self.sent_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<SMSLog {self.status} to {self.phone_number}>"
