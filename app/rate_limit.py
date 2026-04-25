import time
from typing import Dict


class RateLimitExceeded(Exception):
    def __init__(self, retry_after: int) -> None:
        super().__init__("rate_limited")
        self.retry_after = retry_after


class SimpleRateLimiter:
    """In-memory token bucket style rate limiter keyed by client identifier."""

    def __init__(self, capacity: int, refill_rate_per_sec: float, retry_after: int = 5) -> None:
        self.capacity = capacity
        self.refill_rate = refill_rate_per_sec
        self.retry_after = retry_after
        self.tokens: Dict[str, float] = {}
        self.last_refill: Dict[str, float] = {}

    def allow(self, key: str) -> None:
        now = time.time()
        last = self.last_refill.get(key, now)
        self.last_refill[key] = now
        self.tokens[key] = min(
            self.capacity, self.tokens.get(key, self.capacity) + (now - last) * self.refill_rate
        )
        if self.tokens[key] < 1:
            raise RateLimitExceeded(self.retry_after)
        self.tokens[key] -= 1
