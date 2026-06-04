"""Layer 3 — Interface Adapter: sliding-window rate limiter, no external dependencies."""
from __future__ import annotations
import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, max_messages: int = 12, window_sec: int = 60) -> None:
        self._max = max_messages
        self._window = window_sec
        self._store: defaultdict[int, deque[float]] = defaultdict(deque)

    def _prune(self, user_id: int) -> None:
        cutoff = time.time() - self._window
        dq = self._store[user_id]
        while dq and dq[0] < cutoff:
            dq.popleft()

    def is_allowed(self, user_id: int) -> bool:
        self._prune(user_id)
        dq = self._store[user_id]
        if len(dq) < self._max:
            dq.append(time.time())
            return True
        return False

    def seconds_until_allowed(self, user_id: int) -> int:
        self._prune(user_id)
        dq = self._store[user_id]
        if not dq or len(dq) < self._max:
            return 0
        wait = self._window - (time.time() - dq[0])
        return max(1, int(wait) + 1)
