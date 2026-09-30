from dataclasses import dataclass


@dataclass
class ProviderResult:
    success: bool
    provider_message_id: str | None = None
    error_message: str | None = None


class SMSProvider:
    """Common interface for SMS providers."""

    name = "base"

    def send_sms(
        self, phone_number: str, message: str, sender_id: str | None = None
    ) -> ProviderResult:
        raise NotImplementedError


class SMSProviderError(Exception):
    pass


class ProviderNotImplementedError(SMSProviderError):
    pass
