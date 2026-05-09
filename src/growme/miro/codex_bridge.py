"""subprocess-based bridge to the Codex CLI + Miro MCP server.

Python writes a MiroPlan JSON to disk; this module shells out to `codex exec`
with a prompt that tells Codex to apply each item via the configured Miro MCP
server. Honors USE_LIVE_MIRO: when false, returns a dry-run result without
invoking the subprocess (used by tests/CI; Codex is not a CI dependency).
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from pydantic import BaseModel, Field


class CodexResult(BaseModel):
    status: str   # "ok" | "error" | "dry_run"
    plan_path: str
    stdout: str
    stderr: str
    exit_code: int = 0
    item_ids: dict[str, str] = Field(default_factory=dict)


_KEY_ID_RE = re.compile(r"^([\w.\-]+)=([\w\-]+)$", re.MULTILINE)


def _live() -> bool:
    return os.environ.get("USE_LIVE_MIRO", "true").lower() == "true"


def _build_prompt(plan_path: Path, board_id: str) -> str:
    return (
        f"Read the JSON plan at {plan_path.resolve()}. The plan describes Miro items "
        f"to create on board {board_id}. For every item in the plan (frames, slides, "
        f"polls, documents, cards, stickies), in declared order, call the appropriate "
        f"mcp__miro__* tool from the configured Miro MCP server. Apply each item exactly "
        f"as specified — do not skip, do not reorder, do not add. For child items, look up "
        f"the parent frame's miro_id from the parent_key. For every created item, print one "
        f"line `KEY=MIRO_ID` to stdout where KEY is the item's `key` and MIRO_ID is the id "
        f"returned by Miro. When all items are applied successfully, print BUILD COMPLETE "
        f"on a final line and exit."
    )


def apply_plan(plan_path: Path, *, board_id: str, timeout: int = 300) -> CodexResult:
    """Apply a MiroPlan via codex exec. Honors USE_LIVE_MIRO."""
    plan_path = Path(plan_path)
    if not plan_path.exists():
        raise FileNotFoundError(f"plan file not found: {plan_path}")

    if not _live():
        return CodexResult(
            status="dry_run",
            plan_path=str(plan_path),
            stdout="",
            stderr="",
            exit_code=0,
        )

    prompt = _build_prompt(plan_path, board_id)
    proc = subprocess.run(
        ["codex", "exec", prompt],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    item_ids = {m.group(1): m.group(2) for m in _KEY_ID_RE.finditer(proc.stdout)}
    ok = proc.returncode == 0 and "BUILD COMPLETE" in proc.stdout
    return CodexResult(
        status="ok" if ok else "error",
        plan_path=str(plan_path),
        stdout=proc.stdout,
        stderr=proc.stderr,
        exit_code=proc.returncode,
        item_ids=item_ids,
    )
