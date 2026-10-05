"""Login rate limiting (brute-force protection).

A small, dependency-free, in-process throttle for the login endpoint. It uses
a fixed/sliding window keyed on the client IP and the normalized email address
so an attacker cannot trivially bypass it by changing a single value.

Important deployment caveat: state lives in the current process only. With
multiple workers/instances (e.g. several gunicorn workers or several Railway
instances) each process keeps its own counters, so this is NOT a globally
distributed limiter. For a single small-business deployment this is adequate;
a shared store (e.g. Redis) would be required for strict multi-instance
coordination.
"""

import threading
import time

from flask import request


def _ip_key(ip: str) -> str:
    return f"ip:{ip}"


def _pair_key(ip: str, email: str) -> str:
    return f"login:{ip}:{email}"


class _Window:
    """Sliding window of failure timestamps for a single key."""

    def __init__(self, window_seconds: float, clock):
        self._window_seconds = window_seconds
        self._clock = clock
        self._hits = []

    def _prune(self, now: float) -> None:
        cutoff = now - self._window_seconds
        while self._hits and self._hits[0] <= cutoff:
            self._hits.pop(0)

    def count(self, now: float) -> int:
        self._prune(now)
        return len(self._hits)

    def record(self, now: float) -> None:
        self._prune(now)
        self._hits.append(now)

    def seconds_until_reset(self, now: float) -> int:
        self._prune(now)
        if not self._hits:
            return 0
        return max(1, int(self._window_seconds - (now - self._hits[0])) + 1)


class LoginRateLimiter:
    """Tracks failed login attempts and reports when to throttle.

    Two independent thresholds are enforced:

    * per (ip, email) — ``max_attempts`` (default 5)
    * per ip          — ``ip_max_attempts`` (default 25)

    A successful login clears the per-(ip, email) counter (a user who proves
    they know their password is not penalized). Successful logins never count
    as failures.
    """

    def __init__(
        self,
        max_attempts: int = 5,
        ip_max_attempts: int = 25,
        window_seconds: float = 300,
        clock=None,
    ):
        self._max_attempts = max_attempts
        self._ip_max_attempts = ip_max_attempts
        self._window_seconds = window_seconds
        self._clock = clock or time.monotonic
        self._lock = threading.Lock()
        self._windows = {}

    def is_limited(self, ip: str, email: str) -> tuple[bool, int | None]:
        """Return (limited, retry_after_seconds)."""
        now = self._clock()
        with self._lock:
            ip_count = self._count(_ip_key(ip), now)
            if ip_count >= self._ip_max_attempts:
                return True, self._retry_after(_ip_key(ip), now)

            pair_count = self._count(_pair_key(ip, email), now)
            if pair_count >= self._max_attempts:
                return True, self._retry_after(_pair_key(ip, email), now)

            return False, None

    def record_failure(self, ip: str, email: str) -> None:
        now = self._clock()
        with self._lock:
            self._record(_ip_key(ip), now)
            self._record(_pair_key(ip, email), now)

    def record_success(self, ip: str, email: str) -> None:
        with self._lock:
            self._windows.pop(_pair_key(ip, email), None)

    def _window(self, key: str) -> _Window:
        win = self._windows.get(key)
        if win is None:
            win = _Window(self._window_seconds, self._clock)
            self._windows[key] = win
        return win

    def _count(self, key: str, now: float) -> int:
        win = self._windows.get(key)
        return win.count(now) if win is not None else 0

    def _record(self, key: str, now: float) -> None:
        self._window(key).record(now)

    def _retry_after(self, key: str, now: float) -> int | None:
        win = self._windows.get(key)
        if win is None:
            return None
        return win.seconds_until_reset(now)


def client_ip() -> str:
    return request.remote_addr or "unknown"
