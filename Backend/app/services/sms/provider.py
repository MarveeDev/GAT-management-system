from flask import current_app

from app.services.sms.base import ProviderNotImplementedError
from app.services.sms.gonline import GOnlineSMSProvider
from app.services.sms.mock import MockSMSProvider


def get_sms_provider():
    """Return the configured SMS provider.

    ``mock`` is the default development/test provider. ``gonline`` connects to
    the real GONLINE SMS API. Any other configured provider name fails safely
    so that a not-yet-implemented provider can never silently send through the
    mock implementation.
    """
    name = (current_app.config.get("SMS_PROVIDER") or "mock").strip().lower()
    if name == "mock":
        return MockSMSProvider(
            fail=bool(current_app.config.get("SMS_MOCK_FAIL", False))
        )
    if name == "gonline":
        return GOnlineSMSProvider(
            api_key=current_app.config.get("SMS_API_KEY") or "",
            sender_id=current_app.config.get("SMS_SENDER_ID") or "",
        )
    raise ProviderNotImplementedError(f"SMS provider '{name}' is not implemented.")
