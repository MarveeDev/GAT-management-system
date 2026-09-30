import re

from app.extensions import db
from app.models.sms_template import SMSTemplate

PURCHASE_THANK_YOU = "PURCHASE_THANK_YOU"

DEFAULT_PURCHASE_MESSAGE = (
    "Hi {{customer_name}}, thank you for purchasing {{product}} "
    "for GHS {{amount}} at {{shop_name}}. We appreciate your business."
)

VARIABLES = {"customer_name", "shop_name", "product", "amount"}

_VAR_RE = re.compile(r"\{\{\s*([^{}]+?)\s*\}\}")


def get_active_purchase_template() -> SMSTemplate | None:
    return (
        SMSTemplate.query.filter_by(name=PURCHASE_THANK_YOU, is_active=True)
        .order_by(SMSTemplate.created_at.desc())
        .first()
    )


def ensure_default_template() -> SMSTemplate:
    """Create the default active purchase template if it does not exist."""
    existing = SMSTemplate.query.filter_by(name=PURCHASE_THANK_YOU).first()
    if existing is not None:
        return existing

    template = SMSTemplate(
        name=PURCHASE_THANK_YOU,
        message=DEFAULT_PURCHASE_MESSAGE,
        is_active=True,
    )
    db.session.add(template)
    db.session.commit()
    return template


def render_template(template_text: str, context: dict) -> str:
    """Substitute only known variables; unknown tokens are left unchanged.

    This is explicit string replacement — no code execution.
    """

    def repl(match):
        var = match.group(1).strip()
        if var in VARIABLES:
            return str(context.get(var, ""))
        return match.group(0)

    return _VAR_RE.sub(repl, template_text or "")
