from app.extensions import db
from app.models.base import BaseModel


class Customer(BaseModel):
    __tablename__ = "customers"

    name = db.Column(db.String(150), nullable=False)
    phone = db.Column(db.String(50), nullable=True, index=True)
    email = db.Column(db.String(255), nullable=True)

    purchases = db.relationship("Purchase", back_populates="customer")
    sms_logs = db.relationship("SMSLog", back_populates="customer")

    def __repr__(self) -> str:
        return f"<Customer {self.name}>"
