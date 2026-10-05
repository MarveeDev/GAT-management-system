import io
import urllib.error
import urllib.parse
import urllib.request
from unittest.mock import patch

import pytest

from app.services.sms import GOnlineSMSProvider, get_sms_provider


class FakeResponse:
    def __init__(self, body_bytes):
        self._body = body_bytes

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return self._body


def _captured_params(urlopen_mock):
    request = urlopen_mock.call_args[0][0]
    return urllib.parse.parse_qs(request.data.decode("utf-8"))


def _provider(api_key="test-secret-key", sender_id="GAT"):
    return GOnlineSMSProvider(api_key=api_key, sender_id=sender_id)


# --- success ---


def test_gonline_success():
    provider = _provider()
    with patch("urllib.request.urlopen") as urlopen:
        urlopen.return_value = FakeResponse(b'{"code":"OK","message_id":"msg-123"}')
        result = provider.send_sms("233244000000", "Hello")

        assert result.success is True
        assert result.provider_message_id == "msg-123"
        assert result.error_message is None

        params = _captured_params(urlopen)
        assert params["action"] == ["send-sms"]
        assert params["to"] == ["+233244000000"]
        assert params["from"] == ["GAT"]
        assert params["sms"] == ["Hello"]
        assert params["api_key"] == ["test-secret-key"]


def test_gonline_correct_message_is_sent():
    provider = _provider()
    message = "Thank you John for your purchase. We appreciate your business."
    with patch("urllib.request.urlopen") as urlopen:
        urlopen.return_value = FakeResponse(b'{"code":"OK","message_id":"m1"}')
        provider.send_sms("233244000000", message)
        assert _captured_params(urlopen)["sms"] == [message]


# --- success code casing (real API returns lowercase "ok") ---


@pytest.mark.parametrize("code", ["OK", "ok", "Ok", "oK", " ok ", "OK "])
def test_gonline_success_code_casing(code):
    provider = _provider()
    body = (f'{{"code":"{code}","message_id":"msg-cased"}}').encode("utf-8")
    with patch("urllib.request.urlopen") as urlopen:
        urlopen.return_value = FakeResponse(body)
        result = provider.send_sms("233244000000", "Hello")
        assert result.success is True
        assert result.provider_message_id == "msg-cased"


def test_gonline_non_ok_codes_are_not_success():
    provider = _provider()
    for code in ["okay", "success", "200"]:
        body = (f'{{"code":"{code}"}}').encode("utf-8")
        with patch("urllib.request.urlopen") as urlopen:
            urlopen.return_value = FakeResponse(body)
            result = provider.send_sms("233244000000", "Hello")
            assert result.success is False, f"code {code!r} must not be treated as success"


# --- phone format ---


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("0244000000", "+233244000000"),
        ("233244000000", "+233244000000"),
        ("+233244000000", "+233244000000"),
    ],
)
def test_gonline_phone_format(raw, expected):
    provider = _provider()
    with patch("urllib.request.urlopen") as urlopen:
        urlopen.return_value = FakeResponse(b'{"code":"OK"}')
        provider.send_sms(raw, "Hi")
        assert _captured_params(urlopen)["to"] == [expected]


def test_gonline_invalid_phone_number():
    provider = _provider()
    result = provider.send_sms("", "Hello")
    assert result.success is False
    assert "invalid recipient" in result.error_message


# --- error codes ---


@pytest.mark.parametrize(
    "code,fragment",
    [
        ("102", "authentication failed"),
        ("103", "invalid recipient"),
        ("105", "insufficient balance"),
        ("106", "invalid Sender ID"),
    ],
)
def test_gonline_error_codes(code, fragment):
    provider = _provider()
    body = (f'{{"code":"{code}"}}').encode("utf-8")
    with patch("urllib.request.urlopen") as urlopen:
        urlopen.return_value = FakeResponse(body)
        result = provider.send_sms("233244000000", "Hello")
        assert result.success is False
        assert fragment in result.error_message


# --- transport failures ---


def test_gonline_timeout():
    provider = _provider()
    with patch("urllib.request.urlopen", side_effect=TimeoutError()):
        result = provider.send_sms("233244000000", "Hello")
        assert result.success is False
        assert "timed out" in result.error_message


def test_gonline_network_failure():
    provider = _provider()
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("boom")):
        result = provider.send_sms("233244000000", "Hello")
        assert result.success is False
        assert "network error" in result.error_message


def test_gonline_malformed_response():
    provider = _provider()
    with patch("urllib.request.urlopen") as urlopen:
        urlopen.return_value = FakeResponse(b"not-json")
        result = provider.send_sms("233244000000", "Hello")
        assert result.success is False
        assert "invalid response" in result.error_message


def test_gonline_http_error():
    provider = _provider()
    error = urllib.error.HTTPError(
        "https://sms.gonlinesites.com/app/sms/api", 500, "Server Error", {}, io.BytesIO(b"")
    )
    with patch("urllib.request.urlopen", side_effect=error):
        result = provider.send_sms("233244000000", "Hello")
        assert result.success is False
        assert "HTTP error" in result.error_message


# --- security ---


def test_gonline_does_not_leak_api_key():
    provider = _provider(api_key="super-secret-key")
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("boom")):
        result = provider.send_sms("233244000000", "Hello")
    assert "super-secret-key" not in (result.error_message or "")
    assert "super-secret-key" not in (result.provider_message_id or "")


def test_gonline_missing_api_key():
    provider = GOnlineSMSProvider(api_key="", sender_id="GAT")
    result = provider.send_sms("233244000000", "Hello")
    assert result.success is False
    assert "missing API key" in result.error_message


# --- factory ---


def test_provider_factory_selects_gonline(app):
    app.config["SMS_PROVIDER"] = "gonline"
    app.config["SMS_API_KEY"] = "secret"
    app.config["SMS_SENDER_ID"] = "GAT"
    with app.app_context():
        assert isinstance(get_sms_provider(), GOnlineSMSProvider)


def test_provider_factory_defaults_sender_gat(app):
    app.config["SMS_PROVIDER"] = "gonline"
    app.config["SMS_API_KEY"] = "secret"
    app.config["SMS_SENDER_ID"] = ""
    with app.app_context():
        provider = get_sms_provider()
        assert isinstance(provider, GOnlineSMSProvider)
        assert provider._sender_id == "GAT"
