import uuid

from app.services.sms.base import ProviderResult, SMSProvider


class MockSMSProvider(SMSProvider):
    """Development/test provider that never contacts an external service."""

    name = "mock"

    def __init__(self, fail: bool = False):
        self._fail = fail

    def send_sms(self, phone_number, message, sender_id=None):
        if self._fail:
            return ProviderResult(
                success=False, error_message="Mock provider simulated failure."
            )
        return ProviderResult(
            success=True, provider_message_id=f"mock-message-{uuid.uuid4()}"
        )
