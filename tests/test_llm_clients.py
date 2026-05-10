"""LLM client returns the right model id per role; pure logic, no API calls."""
from pydantic import BaseModel

from growme import llm_clients
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


def test_complete_json_repairs_truncated_output(monkeypatch):
    class M(BaseModel):
        terms: list[str]

    truncated = '{"terms": ["alpha", "beta", "gam'  # cut mid-string
    monkeypatch.setattr(llm_clients, "complete", lambda *a, **kw: truncated)
    out = llm_clients.complete_json(role="research_extract", system="", user="", schema=M)
    assert out.terms[:2] == ["alpha", "beta"]


def test_complete_json_passes_through_valid_output(monkeypatch):
    class M(BaseModel):
        terms: list[str]

    monkeypatch.setattr(llm_clients, "complete", lambda *a, **kw: '{"terms": ["x", "y"]}')
    out = llm_clients.complete_json(role="research_extract", system="", user="", schema=M)
    assert out.terms == ["x", "y"]


def test_complete_json_tolerates_raw_newlines_in_strings(monkeypatch):
    """Llama-class models often emit literal newlines inside long markdown fields.

    Pydantic-core's strict JSON parser rejects these; we fall back to
    json.loads(strict=False) before retrying the LLM. Regression for the
    DesignDoc generation failure observed 2026-05-09.
    """
    class M(BaseModel):
        body_md: str

    raw = '{"body_md": "## Heading\n\nParagraph one.\n\nParagraph two."}'
    monkeypatch.setattr(llm_clients, "complete", lambda *a, **kw: raw)
    out = llm_clients.complete_json(role="design_doc", system="", user="", schema=M)
    assert out.body_md.startswith("## Heading")
    assert "Paragraph two." in out.body_md
