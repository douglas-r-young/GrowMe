"""LLM client returns the right model id per role; pure logic, no API calls."""
from growme.llm_clients import resolve_model_for_role, ROLE_TO_MODEL


def test_role_map_covers_all_roles():
    assert set(ROLE_TO_MODEL.keys()) == {
        "research_extract",
        "research_synth",
        "design_doc",
        "session_plan",
        "materials",
        "deck_planner",
        "nudges",
        "delta_report",
        "manager_briefing",   # Phase β: 1:1 prompt-sheet generation
        "deck_auditor",       # Phase γ: anti-slop checklist pass on deck plan
    }


def test_resolve_returns_string_id():
    for role in ROLE_TO_MODEL:
        model_id = resolve_model_for_role(role)
        assert isinstance(model_id, str) and "/" in model_id  # provider/model format


def test_unknown_role_raises():
    import pytest
    with pytest.raises(KeyError):
        resolve_model_for_role("does_not_exist")
