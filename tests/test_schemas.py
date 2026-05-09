"""Schema construction smoke tests — guard against shape regressions."""
import pytest
from pydantic import ValidationError

from growme.schemas import (
    WizardInputs,
    BehaviorTemplate,
    ResearchQuestions,
    CitedFact,
    BehaviorFindings,
    BehaviorContext,
    BaseCompanyResearch,
    EnrichedContext,
    DesignDoc,
    AgendaBlock,
    SessionPlan,
    SessionMaterials,
    LearnerResponse,
    Nudge,
    BehaviorMovement,
    DeltaReport,
)


def test_wizard_inputs_requires_three_behaviors():
    inputs = WizardInputs(
        company_url="neon.tech",
        company_alias="Photon DB",
        audience_description="12 mid-market AEs",
        selected_behavior_ids=["a", "b", "c"],
    )
    assert inputs.program_length_sessions == 4
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
        session_number=4,
        title="Integration",
        behavior_id=None,
        learning_objective="Combine all three behaviors in a deal motion",
        agenda=[
            AgendaBlock(name="Opening hook", duration_min=5, description="..."),
        ],
    )
    assert plan.behavior_id is None
