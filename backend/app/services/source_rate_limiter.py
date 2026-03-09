from collections import deque
from dataclasses import dataclass
from threading import Lock
import time


@dataclass
class RateLimitExceededError(Exception):
    source: str
    limit: int
    window_seconds: int

    def __str__(self) -> str:
        return f"rate limit exceeded for {self.source}: {self.limit}/{self.window_seconds}s"


class SlidingWindowRateLimiter:
    def __init__(self, window_seconds: int = 60):
        self.window_seconds = window_seconds
        self._lock = Lock()
        self._events: dict[str, deque[float]] = {}

    def acquire_or_raise(self, source: str, limit: int, now: float | None = None) -> None:
        if limit <= 0:
            raise RateLimitExceededError(source=source, limit=limit, window_seconds=self.window_seconds)

        ts = now if now is not None else time.time()
        with self._lock:
            queue = self._events.setdefault(source, deque())
            cutoff = ts - self.window_seconds
            while queue and queue[0] <= cutoff:
                queue.popleft()

            if len(queue) >= limit:
                raise RateLimitExceededError(source=source, limit=limit, window_seconds=self.window_seconds)

            queue.append(ts)


rate_limiter = SlidingWindowRateLimiter(window_seconds=60)
