from sqlalchemy import CheckConstraint

from app.extensions import db
from app.models.base import BaseModel


class UserRole:
    SUPER_ADMIN = "SUPER_ADMIN"
    SHOP_MANAGER = "SHOP_MANAGER"
    STAFF = "STAFF"

    VALUES = (SUPER_ADMIN, SHOP_MANAGER, STAFF)


class UserStatus:
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

    VALUES = (ACTIVE, INACTIVE)


class User(BaseModel):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "role IN ('SUPER_ADMIN', 'SHOP_MANAGER', 'STAFF')",
            name="ck_users_role",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'INACTIVE')", name="ck_users_status"
        ),
    )

    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)
    phone = db.Column(db.String(50), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), nullable=False)
    shop_id = db.Column(
        db.String(36), db.ForeignKey("shops.id"), nullable=True, index=True
    )
    status = db.Column(db.String(20), nullable=False, default=UserStatus.ACTIVE)

    shop = db.relationship("Shop", back_populates="users")
    purchases = db.relationship("Purchase", back_populates="staff")
    sms_templates = db.relationship("SMSTemplate", back_populates="creator")
    audit_logs = db.relationship("AuditLog", back_populates="user")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
            "shop_id": self.shop_id,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<User {self.email}>"
