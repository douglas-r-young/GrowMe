"""Layout kinds + the canonical 16-slide story arc skeleton.

The renderer in `pptx.py` dispatches on `LayoutKind`. The planner in `llm.py`
must emit slides in `STORY_ARC_SKELETON` order so tests can assert determinism.
"""
from __future__ import annotations

from typing import Literal

LayoutKind = Literal[
    "cover",
    "section_divider",
    "teach",
    "example",
    "activity",
    "stat",
    "poll_qr",
    "close",
]

# 14 content slides + 2 QR slides = 16. Order matches the plan file.
# Tuples are (layout, role) where role tells the planner what content to fill.
STORY_ARC_SKELETON: list[tuple[LayoutKind, str]] = [
    ("cover", "session cover"),
    ("poll_qr", "pre-program assessment"),
    ("teach", "why this session — frame the customer pain"),
    ("section_divider", "behavior 1 divider"),
    ("teach", "behavior 1 — teach the technique"),
    ("example", "behavior 1 — concrete before/after example"),
    ("activity", "behavior 1 — try it (discussion or role-play)"),
    ("section_divider", "behavior 2 divider"),
    ("teach", "behavior 2 — teach the technique"),
    ("example", "behavior 2 — concrete before/after example"),
    ("activity", "behavior 2 — try it"),
    ("section_divider", "behavior 3 divider"),
    ("teach", "behavior 3 — teach the technique"),
    ("example", "behavior 3 — concrete before/after example"),
    ("activity", "behavior 3 — try it"),
    ("activity", "integration role-play across all three behaviors"),
    ("poll_qr", "post-program assessment"),
    ("close", "thanks + next-week nudge"),
]


# Slides whose `image_prompt` field should be filled by the planner.
LAYOUTS_WITH_IMAGES: frozenset[LayoutKind] = frozenset({"cover", "section_divider"})
