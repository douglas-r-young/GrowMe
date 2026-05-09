"""Pydantic schemas for the GrowMe pipeline. All LLM outputs validate here."""
from typing import Literal, TypedDict

from pydantic import BaseModel, Field, field_validator


# === INPUTS ===

class WizardInputs(BaseModel):
    company_url: str
    company_alias: str
    audience_description: str
    selected_behavior_ids: list[str]
    program_length_sessions: int = 4
    session_duration_min: int = 60

    @field_validator("selected_behavior_ids")
    @classmethod
    def _three_behaviors(cls, v: list[str]) -> list[str]:
        if len(v) != 3:
            raise ValueError("Exactly 3 behaviors must be selected")
        return v


# === BEHAVIOR MENU ===

class ResearchQuestions(BaseModel):
    examples: str
    baselines: str
    objections: str
    proof_points: str


class BehaviorTemplate(BaseModel):
    id: str
    name: str
    description: str
    framework_origin: str
    research_questions: ResearchQuestions


# === RESEARCH OUTPUT ===

class CitedFact(BaseModel):
    text: str
    source: str
    confidence: Literal["high", "medium", "low"]


class BehaviorFindings(BaseModel):
    examples: list[CitedFact] = Field(default_factory=list, max_length=5)
    baselines: list[CitedFact] = Field(default_factory=list, max_length=3)
    objections: list[CitedFact] = Field(default_factory=list, max_length=5)
    proof_points: list[CitedFact] = Field(default_factory=list, max_length=5)


class BehaviorContext(BaseModel):
    behavior_id: str
    behavior_name: str
    behavior_description: str
    framework_origin: str
    research_questions: list[str]
    findings: BehaviorFindings


class BaseCompanyResearch(BaseModel):
    company_snapshot: str
    customer_voice: list[CitedFact] = Field(default_factory=list)
    vertical_vocab: list[str] = Field(default_factory=list)
    named_competitors: list[CitedFact] = Field(default_factory=list)


class EnrichedContext(BaseModel):
    base: BaseCompanyResearch
    per_behavior: list[BehaviorContext]
    sources_used: list[str] = Field(default_factory=list)
    research_timestamp: str


# === DESIGN DOC ===

class DesignDoc(BaseModel):
    audience_section_md: str
    behavior_objectives: list[str]
    learning_objectives: list[str]
    full_markdown: str


# === SESSIONS + MATERIALS ===

class AgendaBlock(BaseModel):
    name: str
    duration_min: int
    description: str


class SessionPlan(BaseModel):
    session_number: int
    title: str
    behavior_id: str | None
    learning_objective: str
    agenda: list[AgendaBlock]


class SessionMaterials(BaseModel):
    session_number: int
    miro_frame_id: str
    slide_frame_ids: list[str]
    pre_poll_id: str
    post_poll_id: str
    facilitator_guide_doc_id: str


# === SIMULATED RUNTIME ===

class LearnerResponse(BaseModel):
    learner_id: str
    learner_name: str
    session_number: int
    pre_poll_answers: dict[str, str]
    post_poll_commitment: str
    nudge_replied: bool


class Nudge(BaseModel):
    learner_id: str
    session_number: int
    email_subject: str
    email_body_md: str
    slack_text: str
    proof_point_used: CitedFact
    miro_card_id: str


class BehaviorMovement(BaseModel):
    behavior_id: str
    pct_moved_from_rarely_to_often: float
    pre_distribution: dict[str, int]
    post_distribution: dict[str, int]


class DeltaReport(BaseModel):
    behavior_movements: list[BehaviorMovement]
    top_objection_still_surfacing: CitedFact
    recommended_reinforcement_md: str
    full_markdown: str
    miro_doc_id: str


# === ORCHESTRATOR STATE ===

class GrowMeState(TypedDict, total=False):
    wizard_inputs: WizardInputs
    miro_board_id: str

    enriched_context: EnrichedContext | None
    design_doc: DesignDoc | None
    design_doc_edited_md: str | None

    session_plans: list[SessionPlan] | None
    materials: list[SessionMaterials] | None

    learner_responses: list[LearnerResponse]
    nudges: list[Nudge]
    delta_report: DeltaReport | None
