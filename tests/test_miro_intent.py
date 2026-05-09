"""MiroPlan round-trip: build → serialize → reload → deep-equal."""
import json
from pathlib import Path

from growme.miro.intent import (
    MiroCard,
    MiroDoc,
    MiroFrame,
    MiroPlan,
    MiroPoll,
    MiroSlide,
    MiroSticky,
    write_plan,
)


def test_miro_plan_roundtrip(tmp_path: Path):
    plan = MiroPlan(
        board_id="o9J_xyz",
        build_step="materials",
        frames=[MiroFrame(key="session_1", title="Session 1: Pain", x=0, y=0)],
        slides=[
            MiroSlide(key="session_1.slide_0", parent_key="session_1",
                      title="Why quantify?", body_md="**Cost** matters.",
                      x=-200, y=-400),
        ],
    )
    path = write_plan(plan, tmp_path / "miro_plan_materials.json")
    reloaded = MiroPlan.model_validate_json(path.read_text())
    assert reloaded == plan


def test_miro_plan_rejects_bad_build_step():
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        MiroPlan(board_id="x", build_step="invalid")  # type: ignore[arg-type]


def test_miro_card_requires_parent_key():
    import pytest
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        MiroCard(key="a", title="b", description_md="c", x=0, y=0)  # parent_key missing
