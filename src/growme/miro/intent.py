"""Pydantic schema for the JSON plan handed to Codex.

Coordinates and parent relationships are pixel-precise — Python computes layout
in plan_builder.py, Codex applies verbatim. Codex makes no layout decisions.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class MiroFrame(BaseModel):
    key: str
    title: str
    x: float
    y: float
    width: int = 1300
    height: int = 1100
    parent_key: None = None  # frames are top-level on the board


class MiroSlide(BaseModel):
    key: str
    parent_key: str
    title: str
    body_md: str
    x: float
    y: float
    width: int = 600


class MiroPoll(BaseModel):
    key: str
    parent_key: str
    kind: Literal["pre", "post_commitment"]
    question: str
    options: list[str]
    x: float
    y: float
    width: int = 400


class MiroDoc(BaseModel):
    key: str
    parent_key: str | None = None  # delta report sits at top level
    title: str
    content_md: str
    x: float
    y: float


class MiroCard(BaseModel):
    key: str
    parent_key: str
    title: str
    description_md: str
    x: float
    y: float


class MiroSticky(BaseModel):
    key: str
    parent_key: str
    content: str
    color: str = "yellow"
    x: float
    y: float


class MiroPlan(BaseModel):
    """Pixel-precise instructions for Codex to apply via mcp__miro__* tools."""
    board_id: str
    build_step: Literal["materials", "nudges", "delta", "header"]
    frames:    list[MiroFrame]    = Field(default_factory=list)
    slides:    list[MiroSlide]    = Field(default_factory=list)
    polls:     list[MiroPoll]     = Field(default_factory=list)
    documents: list[MiroDoc]      = Field(default_factory=list)
    cards:     list[MiroCard]     = Field(default_factory=list)
    stickies:  list[MiroSticky]   = Field(default_factory=list)


def write_plan(plan: MiroPlan, path: Path) -> Path:
    """Serialize the plan to JSON. Returns the written path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(plan.model_dump_json(indent=2))
    return path
