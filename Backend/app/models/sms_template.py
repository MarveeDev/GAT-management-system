from app.extensions import db
from app.models.base import BaseModel


class SMSTemplate(BaseModel):
    __tablename__ = "sms_templates"

    name = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=False)
    created_by = db.Column(
        db.String(36), db.ForeignKey("users.id"), nullable=True, index=True
    )

    creator = db.relationship("User", back_populates="sms_templates")

    def __repr__(self) -> str:
        return f"<SMSTemplate {self.name}>"
