import click
from flask import Flask

from app.extensions import db
from app.models.shop import Shop, ShopStatus
from app.services.user_service import create_super_admin


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

    @app.cli.command("seed-admin")
    def seed_admin() -> None:
        """Interactively create the initial SUPER_ADMIN account."""
        name = click.prompt("Full name").strip()
        email = click.prompt("Email").strip().lower()
        phone = click.prompt("Phone (optional, press Enter to skip)", default="").strip()
        password = click.prompt(
            "Password (min 8 characters)",
            hide_input=True,
            confirmation_prompt=True,
        )

        user, error = create_super_admin(name, email, phone, password)
        if error is not None:
            click.echo(f"Error: {error}")
            return

        click.echo(f"Super admin '{user.email}' created successfully.")
