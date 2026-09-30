from sqlalchemy import CheckConstraint

from app.extensions import db
from app.models.base import BaseModel


class ShopStatus:
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

    VALUES = (ACTIVE, INACTIVE)


class Shop(BaseModel):
    __tablename__ = "shops"
    __table_args__ = (
        CheckConstraint("length(name) > 0", name="ck_shops_name_not_empty"),
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')", name="ck_shops_status"
        ),
    )

    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    sender_id = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(20), nullable=False, default=ShopStatus.ACTIVE)

    users = db.relationship("User", back_populates="shop")
    purchases = db.relationship("Purchase", back_populates="shop")
    sms_logs = db.relationship("SMSLog", back_populates="shop")
    audit_logs = db.relationship("AuditLog", back_populates="shop")

    def __repr__(self) -> str:
        return f"<Shop {self.name}>"
