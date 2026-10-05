import json
import urllib.error
import urllib.parse
import urllib.request

from app.services.customer_service import normalize_phone
from app.services.sms.base import ProviderResult, SMSProvider

# GONLINE SMS API endpoint (POST form-encoded parameters).
GONLINE_ENDPOINT = "https://sms.gonlinesites.com/app/sms/api"

# Reasonable HTTP timeout for provider requests (seconds).
REQUEST_TIMEOUT_SECONDS = 10

# Approved Sender ID for this project when no explicit sender is configured.
DEFAULT_SENDER_ID = "GAT"

# GONLINE error codes -> safe internal messages (never include secrets).
_ERROR_MESSAGES = {
    "100": "GONLINE bad gateway request.",
    "101": "GONLINE wrong action.",
    "102": "GONLINE authentication failed.",
    "103": "GONLINE invalid recipient.",
    "104": "GONLINE coverage inactive.",
    "105": "GONLINE insufficient balance.",
    "106": "GONLINE invalid Sender ID.",
    "109": "GONLINE invalid schedule.",
    "111": "GONLINE message rejected (spam word).",
}


def _to_international(phone: str) -> str | None:
    """Convert the app's normalized number into GONLINE's ``+233...`` format.

    Reuses the existing normalization utility and simply prefixes ``+``. A
    value with no usable digits yields ``None`` so the caller can fail cleanly.
    """
    normalized = normalize_phone(phone)
    if not normalized:
        return None
    return f"+{normalized}"


class GOnlineSMSProvider(SMSProvider):
    """GONLINE SMS provider behind the existing SMSProvider abstraction."""

    name = "gonline"

    def __init__(self, api_key: str, sender_id: str | None = None):
        self._api_key = (api_key or "").strip()
        self._sender_id = (sender_id or "").strip() or DEFAULT_SENDER_ID

    def send_sms(self, phone_number, message, sender_id=None) -> ProviderResult:
        recipient = _to_international(phone_number)
        if recipient is None:
            return ProviderResult(
                success=False, error_message="GONLINE invalid recipient."
            )

        if not self._api_key:
            return ProviderResult(
                success=False,
                error_message="GONLINE not configured (missing API key).",
            )

        from_sender = (sender_id or "").strip() or self._sender_id

        params = {
            "action": "send-sms",
            "api_key": self._api_key,
            "to": recipient,
            "from": from_sender,
            "sms": message,
        }

        data = urllib.parse.urlencode(params).encode("utf-8")
        request = urllib.request.Request(
            GONLINE_ENDPOINT, data=data, method="POST"
        )
        request.add_header("Content-Type", "application/x-www-form-urlencoded")

        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            return ProviderResult(
                success=False,
                error_message=f"GONLINE HTTP error (status {exc.code}).",
            )
        except TimeoutError:
            return ProviderResult(
                success=False, error_message="GONLINE request timed out."
            )
        except urllib.error.URLError:
            return ProviderResult(
                success=False, error_message="GONLINE network error."
            )
        except Exception:
            return ProviderResult(
                success=False, error_message="GONLINE provider error."
            )

        body = self._parse_response(raw)
        if body is None:
            return ProviderResult(
                success=False, error_message="GONLINE invalid response."
            )

        code = str(body.get("code", "")).strip()
        if code.upper() == "OK":
            message_id = body.get("message_id")
            return ProviderResult(
                success=True,
                provider_message_id=str(message_id) if message_id else None,
            )

        return ProviderResult(
            success=False,
            error_message=_ERROR_MESSAGES.get(
                code, f"GONLINE provider error (code {code})."
            ),
        )

    @staticmethod
    def _parse_response(raw: bytes):
        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return None
