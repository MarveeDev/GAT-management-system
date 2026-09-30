from flask import Flask

from app.extensions import db
from app.models.shop import Shop, ShopStatus


def init_cli(app: Flask) -> None:
    @app.cli.command("seed")
    def seed() -> None:
        """Create the initial development shops (idempotent)."""
        shops = [
            {
                "name": "Great Alexender Enterprise \u2014 Main Branch",
                "location": "",
                "phone": "",
                "sender_id": "",
            },
            {
                "name": "Great Alexender Enterprise \u2014 Market Branch",
                "location": "",
                "phone": "",
                "sender_id": "",
            },
            {
                "name": "Great Alexender Enterprise \u2014 City Branch",
                "location": "",
                "phone": "",
                "sender_id": "",
            },
        ]

        created = 0
        for data in shops:
            if Shop.query.filter_by(name=data["name"]).first() is not None:
                continue
            db.session.add(Shop(status=ShopStatus.ACTIVE, **data))
            created += 1

        db.session.commit()
        print(f"Seed complete. Created {created} shop(s).")
