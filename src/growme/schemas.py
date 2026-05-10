"""Pydantic schemas for the GrowMe pipeline. All LLM outputs validate here."""
import re
from typing import Literal, TypedDict

from pydantic import BaseModel, Field, field_validator, model_validator

AgendaBucket = Literal["framework", "story", "activity", "discussion", "buffer"]
NudgeStage = Literal["skeptic", "beginner", "practitioner"]


# === COMMITMENT (structured implementation intention) ===

# Pulls "[Cue] [trigger], I('ll| will) [action]" out of a raw commitment string.
# Cue is one of When / Before / After / If / Once — the canonical Gollwitzer
# habit-stack cues. The trigger is everything between the cue and the first
# comma OR the "I will" clause; the action is everything after the verb cap.
_COMMITMENT_RX = re.compile(
    r"^\s*(?P<cue>when|before|after|if|once)\s+(?P<trigger>.+?)[,\s]+i\s*('ll|’ll|’ll|will)\s+(?P<action>.+?)[\s.]*$",
    re.IGNORECASE | re.DOTALL,
)

CommitmentCue = Literal["When", "Before", "After", "If", "Once"]


class Commitment(BaseModel):
    """Structured view of a Gollwitzer implementation intention.

    Stored as cue + trigger + action so the nudge generator can address them
    precisely ("Your commitment fires when [trigger] — has it happened yet
    this week? Did [action]?"). Cue is one of When / Before / After / If /
    Once — the canonical habit-stack cues. `first_attempt_date` is reserved
    for V1.
    """
    cue: CommitmentCue = "When"
    trigger: str = Field(min_length=2)
    action: str = Field(min_length=2)
    first_attempt_date: str | None = None

    @classmethod
    def from_string(cls, text: str) -> "Commitment":
        """Parse '[Cue] [trigger], I will [action]' into a Commitment.

        Raises ValueError if the input doesn't match the implementation-intention
        form (driven by the same regex `has_implementation_intention` uses, plus
        the banned-vague-trigger check from `pedagogy.checklist`).
        """
        from growme.pedagogy.checklist import has_implementation_intention
        if not has_implementation_intention(text):
            raise ValueError(
                f"Commitment text {text!r} is not a valid implementation intention. "
                "Use 'When/Before/After/If/Once [specific trigger], I will [specific action]' "
                "form. Forbidden vague triggers: 'when I have time', 'whenever I', "
                "'during the week'."
            )
        m = _COMMITMENT_RX.match(text)
        if not m:
            raise ValueError(
                f"Could not parse {text!r} into cue + trigger + action. "
                "Expected 'When/Before/After/If/Once X, I will Y'."
            )
        cue: CommitmentCue = m.group("cue").capitalize()  # type: ignore[assignment]
        return cls(
            cue=cue,
            trigger=m.group("trigger").strip(),
            action=m.group("action").strip(),
        )

    def render(self) -> str:
        """Round-trip back to natural form, preserving the original cue."""
        return f"{self.cue} {self.trigger}, I will {self.action}"


# === INPUTS ===

class WizardInputs(BaseModel):
    company_url: str
    company_alias: str
    audience_description: str
    selected_behavior_ids: list[str]
    reference_urls: list[str] = Field(default_factory=list)
    program_length_sessions: int = 1  # V0 demo: single session covering all 3 behaviors
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
    """V0 ships ONE 60-min integration session covering all 3 behaviors.

    Previously this carried `learning_objectives: list[str]` (length 4 — one per
    session in a 4-session curriculum). The 4-session structure was a historical
    artifact: Linda only ever delivered the integration session. Schema collapsed
    on 2026-05-09 to a single `integration_learning_objective` so the design doc
    matches the deliverable.

    `transfer_plan_md` is a required first-class field (per pedagogy v3 doc §7
    Transfer of Training). The LLM also surfaces it inside `full_markdown` under
    a "## Transfer plan" heading; the standalone field lets downstream consumers
    render it without re-parsing the markdown.
    """
    audience_section_md: str
    behavior_objectives: list[str] = Field(min_length=3, max_length=3)
    integration_learning_objective: str = Field(min_length=20)
    transfer_plan_md: str = Field(min_length=80)
    full_markdown: str

    @field_validator("full_markdown")
    @classmethod
    def _has_transfer_plan_heading(cls, v: str) -> str:
        if "## Transfer plan" not in v and "# Transfer plan" not in v:
            raise ValueError(
                "full_markdown must contain a '## Transfer plan' (or '# Transfer plan') "
                "heading. Per pedagogy v3 doc §7, transfer plan must be a visible top-level "
                "section, not a sub-section."
            )
        return v


# === SESSION PLAN + AGENDA ===

class AgendaBlock(BaseModel):
    name: str
    duration_min: int
    description: str
    bucket: AgendaBucket = "activity"
    """Bucket category drives ratio validation on SessionPlan (framework ≤30% of
    total time, ≥1 buffer block ≥5min, no framework block >12min). Default
    "activity" is the conservative fallback for blocks the LLM forgets to tag."""


class SessionPlan(BaseModel):
    session_number: int
    title: str
    behavior_id: str | None  # None = integration / multi-behavior session
    learning_objective: str
    agenda: list[AgendaBlock]

    @model_validator(mode="after")
    def _enforce_pacing_rules(self) -> "SessionPlan":
        total = sum(b.duration_min for b in self.agenda)
        if total < 55 or total > 65:
            raise ValueError(
                f"Agenda total must be 55-65 minutes (V0 ships ONE 60-min session); "
                f"got {total} min. Per pedagogy v3 doc §6 two-thirds rule, design for "
                f"65-70% time fill on a 60-min session — that's 39-42 explicit minutes "
                f"plus 18-21 min buffer."
            )
        framework_total = sum(b.duration_min for b in self.agenda if b.bucket == "framework")
        if total > 0 and framework_total / total > 0.30:
            raise ValueError(
                f"Framework time ratio {framework_total}/{total} exceeds 30%. "
                f"Per pedagogy v3 doc §5, framework should be 20-30% of session time."
            )
        for b in self.agenda:
            if b.bucket == "framework" and b.duration_min > 12:
                raise ValueError(
                    f"AgendaBlock {b.name!r} has bucket=framework and duration_min="
                    f"{b.duration_min} (>12 min cap). Split it across the session — "
                    f"per pedagogy v3 doc §6, framework blocks cap at 12 min uninterrupted."
                )
        buffers = [b for b in self.agenda if b.bucket == "buffer"]
        if not any(b.duration_min >= 5 for b in buffers):
            raise ValueError(
                "Agenda must have at least one block with bucket='buffer' and "
                "duration_min ≥ 5. Buffer is on schedule, not an oversight — per "
                "pedagogy v3 doc §6 two-thirds rule."
            )
        return self


# === DECK (Streamlit-native materials) ===

SlideKind = Literal["title", "content", "poll_qr", "close"]

# New: layout-driven rendering. `kind` kept for backwards compat with tests/render.
SlideLayout = Literal[
    "cover",
    "section_divider",
    "teach",
    "example",
    "activity",
    "stat",
    "poll_qr",
    "close",
]


class Slide(BaseModel):
    title: str
    body_md: str = ""
    kind: SlideKind = "content"
    qr_url: str | None = None        # only on kind="poll_qr"
    qr_caption: str | None = None    # e.g. "Scan to take pre-assessment"

    # Layout-driven fields (Phase 9.5)
    layout: SlideLayout = "teach"
    # `blocks` carries layout-specific content. Values may be str or list[str].
    # See layouts.py for the placeholder contract per layout.
    blocks: dict[str, object] = Field(default_factory=dict)
    speaker_notes: str = ""
    image_path: str | None = None    # local PNG path for cover/section_divider


class SessionDeck(BaseModel):
    session_number: int = 1
    title: str
    behavior_ids: list[str]                    # the three selected behaviors covered in this session
    slides: list[Slide]
    facilitator_guide_md: str
    manager_briefing_md: str = ""              # Phase β: 1-page "what to ask in your 1:1" doc
    pptx_path: str | None = None               # set after export_pptx writes the file
    pre_qr_url: str
    post_qr_url: str


# === ASSESSMENT (replaces per-session pre/post polls) ===

class FrequencyQuestion(BaseModel):
    behavior_id: str
    prompt: str
    options: list[str] = Field(
        default_factory=lambda: ["Never", "Rarely", "Sometimes", "Often", "Always"]
    )


class ProgramAssessment(BaseModel):
    pre_questions: list[FrequencyQuestion] = Field(min_length=3, max_length=3)
    commitment_options: list[str] = Field(min_length=4, max_length=5)

    @field_validator("commitment_options")
    @classmethod
    def _enforce_implementation_intentions(cls, v: list[str]) -> list[str]:
        from growme.pedagogy.checklist import has_implementation_intention
        bad = [c for c in v if not has_implementation_intention(c)]
        if bad:
            raise ValueError(
                "commitment_options must each use 'When/Before/After/If/Once "
                "[trigger], I will [action]' form (Gollwitzer implementation "
                "intentions). Banned vague triggers: 'when I have time', "
                f"'whenever I', 'during the week'. Offending: {bad!r}"
            )
        return v


class AssessmentResponse(BaseModel):
    session_uuid: str
    learner_id: str
    learner_name: str
    kind: Literal["pre", "post"]
    frequency_answers: dict[str, str]   # behavior_id -> choice (e.g. "Often")
    commitment: Commitment | None = None       # only on kind="post"

    @field_validator("commitment", mode="before")
    @classmethod
    def _coerce_string_to_commitment(cls, v):
        """Accept either a Commitment, a dict, or a raw 'When X, I will Y' string.

        Backwards-compat: existing fixtures + assessment-page free-text inputs
        pass strings; we parse them into structured form server-side. Invalid
        strings raise via `Commitment.from_string` with a helpful error message.
        """
        if v is None or isinstance(v, Commitment):
            return v
        if isinstance(v, dict):
            return v
        if isinstance(v, str):
            return Commitment.from_string(v)
        raise TypeError(
            f"commitment must be Commitment | dict | str | None; got {type(v).__name__}"
        )


# === NUDGES + DELTA ===

class Nudge(BaseModel):
    learner_id: str
    session_number: int = 1
    week_offset: int = Field(default=1, ge=1, le=8)
    """Which week the nudge fires (relative to session). V0 schedules at weeks
    1, 3, 5, 7 weighted toward weeks 2-6 per pedagogy v3 doc §7 transfer cadence."""
    manager_facing: bool = False
    """True = nudge is sent to the rep's manager (1:1 prompt), not the rep."""
    stage_target: NudgeStage = "beginner"
    """Tone calibration for stage-of-change diversity. Skeptic / beginner /
    practitioner — see pedagogy v3 doc §3 Stages of Change."""
    email_subject: str
    email_body_md: str
    slack_text: str
    proof_point_used: CitedFact


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


# === ORCHESTRATOR STATE ===

class GrowMeState(TypedDict, total=False):
    wizard_inputs: WizardInputs

    enriched_context: EnrichedContext | None
    design_doc: DesignDoc | None
    design_doc_edited_md: str | None

    session_plan: SessionPlan | None              # single session in V0
    program_assessment: ProgramAssessment | None
    deck: SessionDeck | None

    assessment_responses: list[AssessmentResponse]
    nudges: list[Nudge]
    delta_report: DeltaReport | None
