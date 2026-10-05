import pytest

from app.models import UserRole
from app.utils.rate_limit import LoginRateLimiter
from tests.helpers import auth_header, make_shop, make_user


class FakeClock:
    def __init__(self, start=1000.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


def login(client, email, password):
    return client.post("/api/auth/login", json={"email": email, "password": password})


# --- unit tests for the limiter -------------------------------------------


def test_limiter_triggers_after_max_attempts():
    clock = FakeClock()
    limiter = LoginRateLimiter(
        max_attempts=5, ip_max_attempts=100, window_seconds=300, clock=clock
    )
    for _ in range(5):
        limiter.record_failure("1.2.3.4", "user@example.com")

    limited, retry_after = limiter.is_limited("1.2.3.4", "user@example.com")
    assert limited is True
    assert retry_after is not None and retry_after > 0


def test_limiter_window_expires():
    clock = FakeClock()
    limiter = LoginRateLimiter(
        max_attempts=5, ip_max_attempts=100, window_seconds=300, clock=clock
    )
    for _ in range(5):
        limiter.record_failure("1.2.3.4", "user@example.com")
    assert limiter.is_limited("1.2.3.4", "user@example.com")[0] is True

    clock.advance(301)
    assert limiter.is_limited("1.2.3.4", "user@example.com")[0] is False


def test_limiter_success_resets_pair_window():
    clock = FakeClock()
    limiter = LoginRateLimiter(
        max_attempts=5, ip_max_attempts=100, window_seconds=300, clock=clock
    )
    for _ in range(4):
        limiter.record_failure("1.2.3.4", "user@example.com")

    limiter.record_success("1.2.3.4", "user@example.com")
    assert limiter.is_limited("1.2.3.4", "user@example.com")[0] is False


def test_limiter_ip_threshold_applies_across_emails():
    clock = FakeClock()
    limiter = LoginRateLimiter(
        max_attempts=100, ip_max_attempts=3, window_seconds=300, clock=clock
    )
    for i in range(3):
        limiter.record_failure("1.2.3.4", f"user{i}@example.com")

    limited, _ = limiter.is_limited("1.2.3.4", "new@example.com")
    assert limited is True


# --- HTTP integration tests -----------------------------------------------


def test_valid_login_succeeds(session, client):
    make_shop(session, "Shop A")
    make_user(session, UserRole.SUPER_ADMIN, "admin@example.com")

    resp = login(client, "admin@example.com", "password123")
    assert resp.status_code == 200
    assert "access_token" in resp.get_json()


def test_invalid_login_rejected(session, client):
    make_shop(session, "Shop A")
    make_user(session, UserRole.SUPER_ADMIN, "admin@example.com")

    resp = login(client, "admin@example.com", "wrong-password")
    assert resp.status_code == 401
    assert resp.get_json()["message"] == "Invalid email or password."


def test_repeated_failures_trigger_throttling(session, client):
    make_shop(session, "Shop A")
    make_user(session, UserRole.SUPER_ADMIN, "admin@example.com")

    for _ in range(5):
        resp = login(client, "admin@example.com", "wrong-password")
        assert resp.status_code == 401

    resp = login(client, "admin@example.com", "wrong-password")
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers
    assert int(resp.headers["Retry-After"]) > 0


def test_successful_login_not_counted_as_failure(session, client):
    make_shop(session, "Shop A")
    make_user(session, UserRole.SUPER_ADMIN, "admin@example.com")

    for _ in range(4):
        assert login(client, "admin@example.com", "wrong-password").status_code == 401

    assert login(client, "admin@example.com", "password123").status_code == 200

    # The successful login cleared the counter, so 5 more failures are allowed
    # before throttling kicks in again.
    for _ in range(5):
        assert login(client, "admin@example.com", "wrong-password").status_code == 401

    assert login(client, "admin@example.com", "wrong-password").status_code == 429


def test_other_authenticated_endpoints_unaffected(session, client):
    make_shop(session, "Shop A")
    make_user(session, UserRole.SUPER_ADMIN, "admin@example.com")

    token = login(client, "admin@example.com", "password123").get_json()["access_token"]

    # Authenticated request works.
    resp = client.get("/api/auth/me", headers=auth_header(token))
    assert resp.status_code == 200

    # An unauthenticated request to another endpoint is a normal 401, not 429.
    assert client.get("/api/auth/me").status_code == 401


def test_throttled_response_does_not_leak_account_existence(session, client):
    make_shop(session, "Shop A")
    make_user(session, UserRole.SUPER_ADMIN, "admin@example.com")

    for _ in range(5):
        login(client, "admin@example.com", "wrong-password")
    existing = login(client, "admin@example.com", "wrong-password")

    for _ in range(5):
        login(client, "no-such-user@example.com", "wrong-password")
    missing = login(client, "no-such-user@example.com", "wrong-password")

    assert existing.status_code == 429
    assert missing.status_code == 429
    assert existing.get_json() == missing.get_json()
    assert "email" not in existing.get_json()["message"]
