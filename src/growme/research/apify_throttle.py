"""Account-wide Apify memory budget. Gates concurrent actor.call() invocations.

Apify caps total memory across all running actors per account (8192 MB on the
free plan). Without throttling, parallel research fan-out exceeds the cap and
actors fail with "By launching this job you will exceed the memory limit". We
model the cap as a counting semaphore in 1024 MB slots; each call site declares
its memory footprint and acquires the matching number of slots.
"""
from __future__ import annotations

import math
import os
import threading
from contextlib import contextmanager

_SLOT_MB = 1024


def _budget_slots() -> int:
    mb = int(os.environ.get("APIFY_MEMORY_BUDGET_MB", "6144"))
    return max(1, mb // _SLOT_MB)


_SEM = threading.Semaphore(_budget_slots())


@contextmanager
def apify_slot(memory_mb: int):
    """Acquire ceil(memory_mb / 1024) slots from the global Apify budget."""
    n = max(1, math.ceil(memory_mb / _SLOT_MB))
    acquired = 0
    try:
        for _ in range(n):
            _SEM.acquire()
            acquired += 1
        yield
    finally:
        for _ in range(acquired):
            _SEM.release()
