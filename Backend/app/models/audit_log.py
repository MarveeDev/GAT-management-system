from sqlalchemy import Index

from app.extensions import db
from app.models.base import gen_uuid, utcnow


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_created_at", "created_at"),
    )

    id = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id = db.Column(
        db.String(36), db.ForeignKey("users.id"), nullable=True, index=True
    )
    shop_id = db.Column(
        db.String(36), db.ForeignKey("shops.id"), nullable=True, index=True
    )
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50), nullable=True)
    entity_id = db.Column(db.String(36), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    user = db.relationship("User", back_populates="audit_logs")
    shop = db.relationship("Shop", back_populates="audit_logs")

    def __repr__(self) -> str:
        return f"<AuditLog {self.action}>"
