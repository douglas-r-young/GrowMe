"""Schema construction smoke tests — guard against shape regressions."""
import pytest
from pydantic import ValidationError

from growme.schemas import (
    AgendaBlock,
    AssessmentResponse,
    BehaviorFindings,
    CitedFact,
    FrequencyQuestion,
    ProgramAssessment,
    SessionDeck,
    SessionPlan,
    Slide,
    WizardInputs,
)


def test_wizard_inputs_requires_three_behaviors():
    inputs = WizardInputs(
        company_url="neon.tech",
        company_alias="Photon DB",
        audience_description="12 mid-market AEs",
        selected_behavior_ids=["a", "b", "c"],
    )
    assert inputs.program_length_sessions == 1
    assert inputs.session_duration_min == 60


def test_wizard_inputs_rejects_wrong_behavior_count():
    with pytest.raises(ValidationError):
        WizardInputs(
            company_url="neon.tech",
            company_alias="Photon DB",
            audience_description="...",
            selected_behavior_ids=["a", "b"],
        )


def test_cited_fact_confidence_enum():
    cf = CitedFact(text="x", source="g2:url", confidence="high")
    assert cf.confidence == "high"
    with pytest.raises(ValidationError):
        CitedFact(text="x", source="g2:url", confidence="bogus")


def test_behavior_findings_caps_examples():
    too_many = [
        CitedFact(text=f"e{i}", source="g2:u", confidence="medium")
        for i in range(6)
    ]
    with pytest.raises(ValidationError):
        BehaviorFindings(examples=too_many, baselines=[], objections=[], proof_points=[])


def test_session_plan_integration_session_allows_no_behavior_id():
    plan = SessionPlan(
        session_number=1,
        title="Integration",
        behavior_id=None,
        learning_objective="Combine all three behaviors in a deal motion",
        agenda=[
            AgendaBlock(name="Opening hook", duration_min=5, description="...", bucket="story"),
            AgendaBlock(name="Teach", duration_min=10, description="...", bucket="framework"),
            AgendaBlock(name="Discuss", duration_min=12, description="...", bucket="discussion"),
            AgendaBlock(name="Practice", duration_min=15, description="...", bucket="activity"),
            AgendaBlock(name="Close", duration_min=10, description="...", bucket="activity"),
            AgendaBlock(name="Buffer", duration_min=8, description="Breathing room.", bucket="buffer"),
        ],
    )
    assert plan.behavior_id is None
    assert sum(b.duration_min for b in plan.agenda) == 60


def test_session_plan_rejects_total_outside_55_to_65():
    with pytest.raises(ValidationError, match="55-65"):
        SessionPlan(
            session_number=1,
            title="Tiny",
            behavior_id=None,
            learning_objective="x" * 30,
            agenda=[
                AgendaBlock(name="Opening", duration_min=5, description="...", bucket="story"),
                AgendaBlock(name="Buffer", duration_min=10, description="...", bucket="buffer"),
            ],
        )


def test_session_plan_rejects_framework_over_30_percent():
    with pytest.raises(ValidationError, match="Framework time ratio"):
        SessionPlan(
            session_number=1,
            title="Lecture",
            behavior_id=None,
            learning_objective="x" * 30,
            agenda=[
                AgendaBlock(name="Open", duration_min=5, description="...", bucket="story"),
                AgendaBlock(name="Teach1", duration_min=10, description="...", bucket="framework"),
                AgendaBlock(name="Teach2", duration_min=10, description="...", bucket="framework"),
                AgendaBlock(name="Practice", duration_min=15, description="...", bucket="activity"),
                AgendaBlock(name="Close", duration_min=12, description="...", bucket="activity"),
                AgendaBlock(name="Buffer", duration_min=8, description="...", bucket="buffer"),
            ],
        )


def test_session_plan_rejects_missing_buffer():
    with pytest.raises(ValidationError, match="buffer"):
        SessionPlan(
            session_number=1,
            title="No buffer",
            behavior_id=None,
            learning_objective="x" * 30,
            agenda=[
                AgendaBlock(name="Open", duration_min=5, description="...", bucket="story"),
                AgendaBlock(name="Teach", duration_min=12, description="...", bucket="framework"),
                AgendaBlock(name="Discuss", duration_min=15, description="...", bucket="discussion"),
                AgendaBlock(name="Practice", duration_min=18, description="...", bucket="activity"),
                AgendaBlock(name="Close", duration_min=10, description="...", bucket="activity"),
            ],
        )


def test_slide_poll_qr_carries_qr_url():
    s = Slide(
        title="Pre-assessment",
        body_md="Scan the code below.",
        kind="poll_qr",
        qr_url="http://localhost:8501/?assessment=abc&kind=pre",
        qr_caption="Scan to take pre-assessment",
    )
    assert s.kind == "poll_qr"
    assert s.qr_url == "http://localhost:8501/?assessment=abc&kind=pre"


def test_session_deck_roundtrip():
    deck = SessionDeck(
        title="Photon DB — Behavior Change",
        behavior_ids=["a", "b", "c"],
        slides=[Slide(title="t", body_md="b", kind="title")],
        facilitator_guide_md="# Guide",
        pre_qr_url="http://localhost:8501/?assessment=u&kind=pre",
        post_qr_url="http://localhost:8501/?assessment=u&kind=post",
    )
    reloaded = SessionDeck.model_validate_json(deck.model_dump_json())
    assert reloaded == deck


def test_program_assessment_requires_three_questions():
    with pytest.raises(ValidationError):
        ProgramAssessment(
            pre_questions=[
                FrequencyQuestion(behavior_id="a", prompt="x"),
                FrequencyQuestion(behavior_id="b", prompt="y"),
            ],
            commitment_options=["c1", "c2", "c3", "c4"],
        )


def test_program_assessment_caps_commitment_options_at_five():
    with pytest.raises(ValidationError):
        ProgramAssessment(
            pre_questions=[
                FrequencyQuestion(behavior_id="a", prompt="x"),
                FrequencyQuestion(behavior_id="b", prompt="y"),
                FrequencyQuestion(behavior_id="c", prompt="z"),
            ],
            commitment_options=["c1", "c2", "c3", "c4", "c5", "c6"],
        )


def test_frequency_question_default_options():
    q = FrequencyQuestion(behavior_id="a", prompt="How often?")
    assert q.options == ["Never", "Rarely", "Sometimes", "Often", "Always"]


def test_assessment_response_pre_has_no_commitment():
    r = AssessmentResponse(
        session_uuid="abc",
        learner_id="L1",
        learner_name="Sam",
        kind="pre",
        frequency_answers={"a": "Rarely"},
    )
    assert r.commitment is None


def test_assessment_response_post_carries_commitment():
    r = AssessmentResponse(
        session_uuid="abc",
        learner_id="L1",
        learner_name="Sam",
        kind="post",
        frequency_answers={"a": "Often"},
        commitment="When pipeline review starts, I will state the EB name on my top 3 deals",
    )
    assert r.commitment is not None
    assert r.commitment.trigger == "pipeline review starts"
    assert "EB name" in r.commitment.action
    assert r.commitment.render().startswith("When ")


def test_assessment_response_rejects_non_implementation_intention_commitment():
    with pytest.raises(ValidationError, match="implementation intention"):
        AssessmentResponse(
            session_uuid="abc",
            learner_id="L1",
            learner_name="Sam",
            kind="post",
            frequency_answers={"a": "Often"},
            commitment="Try this on 3 calls this week",
        )


def test_program_assessment_rejects_non_implementation_intention_options():
    with pytest.raises(ValidationError, match="implementation intentions"):
        ProgramAssessment(
            pre_questions=[
                FrequencyQuestion(behavior_id="a", prompt="x"),
                FrequencyQuestion(behavior_id="b", prompt="y"),
                FrequencyQuestion(behavior_id="c", prompt="z"),
            ],
            commitment_options=[
                "Just try harder",
                "When pipeline review starts, I will state the EB",
                "When my Tuesday demo ends, I'll log 3 budget questions",
                "Whenever I remember, I will quantify pain",
            ],
        )
