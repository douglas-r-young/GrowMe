"""Verify the Apify and LLM throttles cap effective concurrency."""
from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor

from growme import llm_clients
from growme.research import apify_throttle


class _PeakCounter:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.active = 0
        self.peak = 0

    def __enter__(self):
        with self.lock:
            self.active += 1
            self.peak = max(self.peak, self.active)
        return self

    def __exit__(self, *exc):
        with self.lock:
            self.active -= 1


def test_apify_slot_caps_concurrency(monkeypatch):
    monkeypatch.setattr(apify_throttle, "_SEM", threading.Semaphore(2))
    counter = _PeakCounter()

    def worker():
        with apify_throttle.apify_slot(1024), counter:
            time.sleep(0.05)

    with ThreadPoolExecutor(max_workers=8) as ex:
        list(ex.map(lambda _: worker(), range(8)))

    assert counter.peak <= 2


def test_apify_slot_acquires_multiple_slots_for_large_jobs(monkeypatch):
    monkeypatch.setattr(apify_throttle, "_SEM", threading.Semaphore(2))
    # A 4096 MB job needs 4 slots — more than the budget — so it must block
    # forever. We verify by racing it against a timeout.
    done = threading.Event()

    def worker():
        with apify_throttle.apify_slot(4096):
            done.set()

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    assert not done.wait(0.2)


def test_llm_provider_semaphore_serializes_featherless(monkeypatch):
    monkeypatch.setitem(llm_clients._PROVIDER_LIMITS, "featherless_ai", threading.Semaphore(1))
    counter = _PeakCounter()

    def fake_completion(**_):
        with counter:
            time.sleep(0.05)

        class _Msg: content = "ok"
        class _Choice: message = _Msg()
        class _Resp: choices = [_Choice()]
        return _Resp()

    monkeypatch.setattr(llm_clients.litellm, "completion", fake_completion)
    monkeypatch.setenv("FEATHERLESS_API_KEY", "x")

    def worker():
        llm_clients.complete("research_synth", "sys", "user")

    with ThreadPoolExecutor(max_workers=6) as ex:
        list(ex.map(lambda _: worker(), range(6)))

    assert counter.peak == 1


def test_llm_openai_calls_are_not_gated(monkeypatch):
    counter = _PeakCounter()

    def fake_completion(**_):
        with counter:
            time.sleep(0.05)

        class _Msg: content = "ok"
        class _Choice: message = _Msg()
        class _Resp: choices = [_Choice()]
        return _Resp()

    monkeypatch.setattr(llm_clients.litellm, "completion", fake_completion)
    monkeypatch.setenv("OPENAI_API_KEY", "x")

    def worker():
        llm_clients.complete("session_plan", "sys", "user")

    with ThreadPoolExecutor(max_workers=4) as ex:
        list(ex.map(lambda _: worker(), range(4)))

    assert counter.peak > 1
