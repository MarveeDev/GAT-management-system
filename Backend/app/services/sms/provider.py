from flask import current_app

from app.services.sms.base import ProviderNotImplementedError
from app.services.sms.mock import MockSMSProvider


def get_sms_provider():
    """Return the configured SMS provider.

    Only ``mock`` is implemented for now. Any other configured provider name
    fails safely so that a not-yet-implemented provider can never silently
    send through the mock implementation.
    """
    name = (current_app.config.get("SMS_PROVIDER") or "mock").strip().lower()
    if name == "mock":
        return MockSMSProvider(
            fail=bool(current_app.config.get("SMS_MOCK_FAIL", False))
        )
    raise ProviderNotImplementedError(f"SMS provider '{name}' is not implemented.")
