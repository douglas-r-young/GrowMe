from __future__ import annotations

import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from growme.api.app import app
from growme.api import store
from growme.decks.llm import DeckPlan, PlannedSlide
from growme.schemas import (
    AgendaBlock,
    BaseCompanyResearch,
    BehaviorContext,
    BehaviorFindings,
    BehaviorMovement,
    CitedFact,
    DeltaReport,
    DesignDoc,
    EnrichedContext,
    FrequencyQuestion,
    Nudge,
    ProgramAssessment,
    SessionDeck,
    SessionPlan,
    Slide,
)


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setenv("GROWME_SESSION_DIR", str(tmp_path / "sessions"))
    monkeypatch.setenv("GROWME_PUBLIC_URL", "http://localhost:5173")
    return TestClient(app)


def _create_session(client: TestClient) -> str:
    response = client.post("/api/sessions")
    assert response.status_code == 200
    return response.json()["session_uuid"]


def _default_ids(client: TestClient) -> list[str]:
    response = client.get("/api/behavior-menu")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["behaviors"]) == 6
    return payload["default_selected_behavior_ids"]


def _wait_for_job(client: TestClient, job_id: str) -> dict:
    deadline = time.time() + 5
    while time.time() < deadline:
        payload = client.get(f"/api/jobs/{job_id}").json()
        if payload["status"] in {"complete", "error"}:
            return payload
        time.sleep(0.02)
    raise AssertionError(f"job {job_id} did not finish")


def _enriched() -> EnrichedContext:
    contexts = []
    for idx, bid in enumerate(_BIDS, start=1):
        contexts.append(
            BehaviorContext(
                behavior_id=bid,
                behavior_name=f"Behavior {idx}",
                behavior_description=f"Do behavior {idx}",
                framework_origin="Test Framework",
                research_questions=["What changes?"],
                findings=BehaviorFindings(
                    examples=[CitedFact(text=f"Example {idx}", source="https://example.test", confidence="high")],
                    baselines=[CitedFact(text=f"Baseline {idx}", source="https://example.test", confidence="medium")],
                    objections=[CitedFact(text=f"Objection {idx}", source="https://example.test", confidence="medium")],
                    proof_points=[CitedFact(text=f"Proof {idx}", source="https://example.test", confidence="high")],
                ),
            )
        )
    return EnrichedContext(
        base=BaseCompanyResearch(
            company_snapshot="Photon DB helps teams ship faster.",
            vertical_vocab=["pipeline"],
        ),
        per_behavior=contexts,
        sources_used=["https://example.test"],
        research_timestamp="2026-05-09T00:00:00Z",
    )


def _design_doc() -> DesignDoc:
    return DesignDoc(
        audience_section_md="## Audience\nEnterprise AEs",
        behavior_objectives=["Objective one", "Objective two", "Objective three"],
        integration_learning_objective="Learners synthesize three behaviors in a realistic deal moment.",
        transfer_plan_md="Managers reinforce commitments over three weeks with check-ins and final survey follow-up.",
        full_markdown=(
            "# Design\n\n## Transfer plan\n\nManagers reinforce commitments over three weeks "
            "with check-ins and final survey follow-up."
        ),
    )


def _session_plan() -> SessionPlan:
    return SessionPlan(
        session_number=1,
        title="Photon DB deal discipline",
        behavior_id=None,
        learning_objective="Learners synthesize all three behaviors in a live deal moment.",
        agenda=[
            AgendaBlock(name="Open", duration_min=5, description="Story", bucket="story"),
            AgendaBlock(name="Teach", duration_min=10, description="Framework", bucket="framework"),
            AgendaBlock(name="Discuss", duration_min=12, description="Discussion", bucket="discussion"),
            AgendaBlock(name="Practice", duration_min=15, description="Practice", bucket="activity"),
            AgendaBlock(name="Commit", duration_min=10, description="Commit", bucket="activity"),
            AgendaBlock(name="Buffer", duration_min=8, description="Buffer", bucket="buffer"),
        ],
    )


def _assessment() -> ProgramAssessment:
    return ProgramAssessment(
        pre_questions=[
            FrequencyQuestion(behavior_id=bid, prompt=f"How often do you practice {bid}?")
            for bid in _BIDS
        ],
        commitment_options=[
            "When my next discovery call starts, I will ask how the buyer measures the problem.",
            "Before naming a product capability in a demo, I will state the customer outcome it serves.",
            "When a prospect names a competitor, I will offer one specific proof point.",
            "After my next pipeline review, I will rewrite one stalled opportunity around business impact.",
        ],
    )


def _planned(layout: str, blocks: dict) -> PlannedSlide:
    return PlannedSlide(layout=layout, blocks=blocks, speaker_notes="Speaker notes " * 12)


def _deck_plan() -> DeckPlan:
    slides = [
        _planned("cover", {"eyebrow": "GrowMe", "title": "Photon DB", "subtitle": "Practice", "image_prompt": "abstract shapes"}),
        _planned("poll_qr", {}),
        _planned("teach", {"eyebrow": "Why", "title": "Why this matters", "bullets": ["A", "B"], "citation": "source"}),
    ]
    for idx in range(1, 4):
        slides.extend(
            [
                _planned("section_divider", {"number": f"0{idx}", "behavior_name": f"Behavior {idx}", "promise": "Promise", "image_prompt": "abstract shapes"}),
                _planned("teach", {"eyebrow": "How", "title": f"Teach {idx}", "bullets": ["A", "B"], "citation": "source"}),
                _planned("example", {"title": f"Example {idx}", "before_body": "Before", "after_body": "After"}),
                _planned("activity", {"eyebrow": "Try it", "title": f"Activity {idx}", "prompt": "Run the scenario", "sub_prompts": ["A"], "timer_hint": "5 min"}),
            ]
        )
    slides.extend(
        [
            _planned("activity", {"eyebrow": "Integration", "title": "Role-play", "prompt": "Combine the behaviors", "sub_prompts": ["A"], "timer_hint": "10 min"}),
            _planned("poll_qr", {}),
            _planned("close", {"title": "Close", "commitment_recap": "Practice the three behaviors.", "next_step": "Try it this week."}),
        ]
    )
    return DeckPlan(slides=slides)


_BIDS = [
    "pic_pbo_quantify_pain",
    "pic_rc_capabilities_outcomes",
    "pic_diff_differentiate",
]


def test_session_setup_and_behavior_validation(client: TestClient) -> None:
    session_id = _create_session(client)
    default_ids = _default_ids(client)

    setup_response = client.put(
        f"/api/sessions/{session_id}/setup",
        json={
            "program_name": "Q2 cohort",
            "company_url": "neon.tech",
            "company_alias": "Photon DB",
            "audience_preset": "Enterprise AEs",
            "audience_cohort": "10-20 participants",
            "audience_program_fmt": "Single session (demo)",
            "audience_notes": "Focus on practical drills.",
            "reference_urls": ["https://example.test"],
            "uploaded_file_names": ["playbook.pdf"],
        },
    )
    assert setup_response.status_code == 200

    bad = client.put(f"/api/sessions/{session_id}/behaviors", json={"selected_behavior_ids": default_ids[:2]})
    assert bad.status_code == 422

    good = client.put(f"/api/sessions/{session_id}/behaviors", json={"selected_behavior_ids": default_ids})
    assert good.status_code == 200

    state_payload = client.get(f"/api/sessions/{session_id}").json()
    assert state_payload["setup"]["program_name"] == "Q2 cohort"
    assert state_payload["setup"]["uploaded_file_names"] == ["playbook.pdf"]
    assert "Target audience: Enterprise AEs" in state_payload["wizard_inputs"]["audience_description"]
    assert state_payload["selected_behavior_ids"] == default_ids


def test_design_and_build_jobs_expose_real_outputs(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_id = _create_session(client)
    client.put(
        f"/api/sessions/{session_id}/setup",
        json={
            "company_url": "neon.tech",
            "company_alias": "Photon DB",
            "audience_preset": "Enterprise AEs",
            "audience_cohort": "10-20 participants",
            "audience_program_fmt": "Single session (demo)",
            "audience_notes": "Focus on practical drills.",
        },
    )
    client.put(f"/api/sessions/{session_id}/behaviors", json={"selected_behavior_ids": _BIDS})

    monkeypatch.setattr("growme.research.node.run", lambda _inputs: _enriched())
    monkeypatch.setattr("growme.design_doc.node.run", lambda _enriched_ctx, _inputs: _design_doc())

    design_job_id = client.post(f"/api/sessions/{session_id}/design-jobs").json()["job_id"]
    assert _wait_for_job(client, design_job_id)["status"] == "complete"

    state_payload = client.get(f"/api/sessions/{session_id}").json()
    assert state_payload["design_doc"]["integration_learning_objective"].startswith("Learners synthesize")
    assert state_payload["design_doc_edited_md"].startswith("# Design")

    def fake_export(deck, out_path: Path):
        out_path.write_bytes(b"pptx bytes")
        deck.pptx_path = str(out_path)
        return out_path

    monkeypatch.setattr("growme.sessions.plan_node.run", lambda _md, _ctx, _inputs: _session_plan())
    monkeypatch.setattr("growme.assessment.generator.generate_program_assessment", lambda _ctx, _inputs: _assessment())
    monkeypatch.setattr("growme.decks.llm.plan_deck_audited", lambda _plan, _ctx: (_deck_plan(), None))
    monkeypatch.setattr("growme.decks.images.generate_deck_images", lambda _prompts: [None, None, None, None])
    monkeypatch.setattr("growme.decks.llm.gen_facilitator_guide", lambda _plan, _ctx, deck_plan=None: "# Facilitator\n\nGuide body")
    monkeypatch.setattr("growme.decks.llm.gen_manager_briefing", lambda **_kwargs: "# Manager\n\nBriefing body")
    monkeypatch.setattr("growme.decks.pptx.export_pptx", fake_export)

    build_job_id = client.post(f"/api/sessions/{session_id}/build-jobs").json()["job_id"]
    assert _wait_for_job(client, build_job_id)["status"] == "complete"

    assets = client.get(f"/api/sessions/{session_id}/assets").json()["assets"]
    asset_ids = {asset["id"] for asset in assets}
    assert {"deck", "facilitator-guide", "manager-briefing", "program-assessment"}.issubset(asset_ids)

    deck_download = client.get(f"/api/sessions/{session_id}/downloads/deck")
    assert deck_download.status_code == 200
    assert deck_download.content == b"pptx bytes"

    snapshot = client.get(f"/api/sessions/{session_id}").json()
    assert snapshot["deck"]["pre_qr_url"] == f"http://localhost:5173/?assessment={session_id}&kind=pre"
    assert snapshot["program_assessment"]["pre_questions"][0]["behavior_id"] == _BIDS[0]


def test_assessment_routes_record_responses_and_checkins(client: TestClient) -> None:
    session_id = _create_session(client)
    store.update(session_id, "selected_behavior_ids", _BIDS)
    store.update(session_id, "program_assessment", _assessment())

    config = client.get(f"/api/assessment/{session_id}/config?kind=pre")
    assert config.status_code == 200
    assert len(config.json()["assessment"]["pre_questions"]) == 3

    pre = client.post(
        f"/api/assessment/{session_id}/pre",
        json={
            "learner_name": "Sam",
            "learner_id": "sam@example.com",
            "frequency_answers": {bid: "Often" for bid in _BIDS},
        },
    )
    assert pre.status_code == 200

    post_config = client.get(f"/api/assessment/{session_id}/config?kind=post").json()
    behavior_id = post_config["commitment_options"][0]["behavior_id"]
    post = client.post(
        f"/api/assessment/{session_id}/post",
        json={
            "learner_name": "Sam",
            "learner_email": "sam@example.com",
            "behavior_id": behavior_id,
        },
    )
    assert post.status_code == 200

    checkin = client.post(
        f"/api/assessment/{session_id}/checkin",
        json={"learner": "sam@example.com", "week": 1, "done": True},
    )
    assert checkin.status_code == 200

    snapshot = client.get(f"/api/sessions/{session_id}").json()
    assert len(snapshot["assessment_responses"]) == 2
    assert snapshot["commitments"]["sam@example.com"]["behavior_id"] == behavior_id
    assert snapshot["checkins"]["sam@example.com"] == [[1, True]]


def test_send_weekly_nudges_uses_roster_and_smtp(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_id = _create_session(client)
    store.update(session_id, "selected_behavior_ids", _BIDS)
    store.update(session_id, "program_assessment", _assessment())
    client.post(
        f"/api/assessment/{session_id}/post",
        json={
            "learner_name": "Sam",
            "learner_email": "sam@example.com",
            "behavior_id": _BIDS[0],
        },
    )

    sent: list[tuple[str, str, str]] = []
    monkeypatch.setattr(
        "growme.email.weekly_nudge.build_email",
        lambda **_kwargs: ("Week 1", "<p>body</p>"),
    )
    monkeypatch.setattr(
        "growme.email.smtp_client.send_email",
        lambda to_email, subject, html: sent.append((to_email, subject, html)),
    )

    response = client.post(f"/api/sessions/{session_id}/nudges/send-week", json={"week": "1"})

    assert response.status_code == 200
    assert response.json()["sent"] == 1
    assert sent == [("sam@example.com", "Week 1", "<p>body</p>")]


def test_behavior_validation_rejects_wrong_count_and_unknown_ids(client: TestClient) -> None:
    session_id = _create_session(client)
    default_ids = _default_ids(client)

    too_few = client.put(f"/api/sessions/{session_id}/behaviors", json={"selected_behavior_ids": default_ids[:2]})
    assert too_few.status_code == 422

    too_many = client.put(
        f"/api/sessions/{session_id}/behaviors",
        json={"selected_behavior_ids": list(default_ids) + ["pic_extra_one"]},
    )
    assert too_many.status_code == 422

    unknown = client.put(
        f"/api/sessions/{session_id}/behaviors",
        json={"selected_behavior_ids": [default_ids[0], default_ids[1], "pic_does_not_exist"]},
    )
    assert unknown.status_code == 422
    assert "pic_does_not_exist" in unknown.json()["detail"]


def test_downloads_404_before_build_and_for_unknown_assets(client: TestClient) -> None:
    session_id = _create_session(client)

    for asset_id, expected_substr in [
        ("deck", "Deck"),
        ("facilitator-guide", "Guide"),
        ("manager-briefing", "Manager"),
        ("program-assessment", "Assessment"),
        ("delta-report", "Delta"),
        ("nudges", "Nudges"),
    ]:
        response = client.get(f"/api/sessions/{session_id}/downloads/{asset_id}")
        assert response.status_code == 404, f"{asset_id} should 404 before build"
        assert expected_substr in response.json()["detail"]

    unknown_asset = client.get(f"/api/sessions/{session_id}/downloads/totally-made-up")
    assert unknown_asset.status_code == 404
    assert unknown_asset.json()["detail"] == "Unknown asset"

    missing_session = client.get("/api/sessions/00000000-0000-0000-0000-000000000000/downloads/deck")
    assert missing_session.status_code == 404

    missing_job = client.get("/api/jobs/00000000-0000-0000-0000-000000000000")
    assert missing_job.status_code == 404


def test_design_job_error_is_surfaced_and_persisted(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_id = _create_session(client)
    client.put(
        f"/api/sessions/{session_id}/setup",
        json={
            "company_url": "neon.tech",
            "company_alias": "Photon DB",
            "audience_preset": "Enterprise AEs",
            "audience_cohort": "10-20 participants",
            "audience_program_fmt": "Single session (demo)",
            "audience_notes": "Focus on practical drills.",
        },
    )
    client.put(f"/api/sessions/{session_id}/behaviors", json={"selected_behavior_ids": _BIDS})

    def boom(_inputs):
        raise RuntimeError("research backend exploded")

    monkeypatch.setattr("growme.research.node.run", boom)

    job_id = client.post(f"/api/sessions/{session_id}/design-jobs").json()["job_id"]
    final = _wait_for_job(client, job_id)
    assert final["status"] == "error"
    assert "research backend exploded" in (final["error"] or "")

    snapshot = client.get(f"/api/sessions/{session_id}").json()
    last_job = snapshot["last_job"]
    assert last_job is not None
    assert last_job["kind"] == "design"
    assert last_job["status"] == "error"
    assert "research backend exploded" in (last_job["error"] or "")


def test_simulation_records_fixture_outputs(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_id = _create_session(client)
    enriched = _enriched()
    deck = SessionDeck(
        title="Photon DB",
        behavior_ids=_BIDS,
        slides=[Slide(title="Cover")],
        facilitator_guide_md="# Guide",
        manager_briefing_md="",
        pre_qr_url=f"http://localhost:5173/?assessment={session_id}&kind=pre",
        post_qr_url=f"http://localhost:5173/?assessment={session_id}&kind=post",
    )
    store.update_many(session_id, {"enriched_context": enriched, "deck": deck})

    proof = CitedFact(text="Proof", source="https://example.test", confidence="high")
    monkeypatch.setattr(
        "growme.nudges.node.generate_for_post_responses",
        lambda _responses, _enriched: [
            Nudge(
                learner_id="sam@example.com",
                email_subject="Try it",
                email_body_md="Try the behavior this week.",
                slack_text="Did you try it?",
                proof_point_used=proof,
            )
        ],
    )
    monkeypatch.setattr(
        "growme.delta_report.node.run",
        lambda _responses, _enriched: DeltaReport(
            behavior_movements=[
                BehaviorMovement(
                    behavior_id=_BIDS[0],
                    pct_moved_from_rarely_to_often=0.25,
                    pre_distribution={"Rarely": 1},
                    post_distribution={"Often": 1},
                )
            ],
            top_objection_still_surfacing=proof,
            recommended_reinforcement_md="- Keep practicing",
            full_markdown="# Behavior Delta Report",
        ),
    )

    response = client.post(f"/api/sessions/{session_id}/simulation")

    assert response.status_code == 200
    payload = response.json()
    assert payload["sim_complete"] is True
    assert payload["nudges"][0]["learner_id"] == "sam@example.com"
    assert payload["delta_report"]["full_markdown"] == "# Behavior Delta Report"
