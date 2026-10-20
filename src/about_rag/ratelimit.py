"""A sliding-window rate limiter, written by hand before reaching for a library.

For each key (a visitor's IP, or "global" for the whole site) it remembers the times of
the requests in the last `window` seconds. A new request is allowed while fewer than
`limit` of those remain. Exact, simple, and small: memory is at most `limit` timestamps
per active key.

It lives in one process's memory, so it resets on restart and isn't shared between
several server processes. One process on a free host is the plan; with several, the
state would move to Redis (same idea, shared storage).
"""

import threading
import time
from collections import deque
from collections.abc import Callable


class RateLimiter:
    def __init__(
        self, limit: int, window: float = 60.0, clock: Callable[[], float] = time.monotonic
    ) -> None:
        if limit <= 0 or window <= 0:
            raise ValueError("limit and window must be positive")
        self.limit = limit
        self.window = window
        self.clock = clock
        self._hits: dict[str, deque[float]] = {}
        self._sweep_at = 1024
        self._lock = threading.Lock()

    def acquire(self, key: str) -> float:
        """Count a request for `key` if it is allowed.

        Returns 0.0 when allowed (and counted), otherwise the seconds to wait (not counted).
        Checking and counting happen under one lock, so two simultaneous requests can't
        both squeeze into the last free slot.
        """
        with self._lock:
            hits = self._prune(key)
            if len(hits) >= self.limit:
                return hits[0] + self.window - self.clock()
            hits.append(self.clock())
            return 0.0

    def __len__(self) -> int:
        """Number of keys currently tracked (for tests and monitoring)."""
        return len(self._hits)

    def _prune(self, key: str) -> deque[float]:
        cutoff = self.clock() - self.window
        if len(self._hits) >= self._sweep_at:
            self._hits = {k: v for k, v in self._hits.items() if v and v[-1] > cutoff}
            self._sweep_at = max(1024, 2 * len(self._hits))
        hits = self._hits.setdefault(key, deque())
        while hits and hits[0] <= cutoff:
            hits.popleft()
        return hits
