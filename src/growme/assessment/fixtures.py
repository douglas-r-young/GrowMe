# src/growme/assessment/fixtures.py
"""8 simulated learners with one pre + one post AssessmentResponse each.

Pre answers skew Rarely/Sometimes; post answers skew Sometimes/Often with
non-uniform movement so the delta has narrative depth (one behavior shifts
more than the other two).

Phase β additions (per pedagogy v3 doc §3 Stages of Change):
- Each learner gets a `stage_of_change` (skeptic / beginner / practitioner) and
  `commitment_strength` (1-5). Distribution: 2 skeptics, 4 beginners, 2 practitioners.
- Commitments use "When [trigger], I will [action]" form (Gollwitzer implementation
  intentions) and are validated by `AssessmentResponse.commitment` — flat strings
  that don't match the form will raise.
- Stage data drives nudge-tone differentiation in `nudges/node.py`.
"""
from __future__ import annotations

from dataclasses import dataclass

from growme.schemas import AssessmentResponse


@dataclass(frozen=True)
class LearnerProfile:
    learner_id: str
    learner_name: str
    stage_of_change: str       # "skeptic" | "beginner" | "practitioner"
    commitment_strength: int   # 1-5; drives tone confidence in nudges


LEARNER_PROFILES: list[LearnerProfile] = [
    LearnerProfile("learner_01", "Sam Patel",      "beginner",      3),
    LearnerProfile("learner_02", "Riya Chen",      "skeptic",       2),
    LearnerProfile("learner_03", "Marcus Vega",    "beginner",      4),
    LearnerProfile("learner_04", "Tasha Brooks",   "skeptic",       2),
    LearnerProfile("learner_05", "Jordan Kim",     "practitioner",  5),
    LearnerProfile("learner_06", "Priya Nair",     "beginner",      3),
    LearnerProfile("learner_07", "Diego Souza",    "practitioner",  4),
    LearnerProfile("learner_08", "Lena Park",      "beginner",      3),
]
"""8 learners, distributed 2 skeptics / 4 beginners / 2 practitioners — the
plausible cohort shape per pedagogy v3 doc §3 ("most rooms have a healthy
precontemplation contingent")."""


# Backwards-compat shape: list of (learner_id, learner_name) tuples. Existing
# code that imported LEARNERS keeps working; new code reads LEARNER_PROFILES.
LEARNERS: list[tuple[str, str]] = [(p.learner_id, p.learner_name) for p in LEARNER_PROFILES]


def profile_for(learner_id: str) -> LearnerProfile:
    """Return the LearnerProfile for `learner_id`. Raises KeyError if missing."""
    for p in LEARNER_PROFILES:
        if p.learner_id == learner_id:
            return p
    raise KeyError(f"unknown learner_id: {learner_id!r}")


# Per-learner pre answers per behavior (b1, b2, b3 — order = wizard order).
_PRE = [
    ("Rarely",    "Rarely",    "Sometimes"),
    ("Sometimes", "Rarely",    "Rarely"),
    ("Rarely",    "Sometimes", "Rarely"),
    ("Rarely",    "Rarely",    "Rarely"),
    ("Sometimes", "Sometimes", "Often"),
    ("Rarely",    "Rarely",    "Sometimes"),
    ("Often",     "Rarely",    "Rarely"),
    ("Rarely",    "Sometimes", "Rarely"),
]
# Post — overall lift, but b1 lifts more than b2 / b3.
_POST = [
    ("Often",     "Sometimes", "Often"),
    ("Often",     "Sometimes", "Sometimes"),
    ("Often",     "Often",     "Sometimes"),
    ("Often",     "Sometimes", "Sometimes"),
    ("Often",     "Often",     "Often"),
    ("Often",     "Sometimes", "Sometimes"),
    ("Often",     "Sometimes", "Sometimes"),
    ("Sometimes", "Often",     "Sometimes"),
]
# Implementation-intention commitments (Gollwitzer form: "When X, I will Y").
# Triggers are event-bound or time-bound. Validated by AssessmentResponse.commitment.
_COMMITMENTS = [
    "When my next discovery call starts, I will ask 'how do you measure that today?' before any capability pitch.",
    "When I open a new opportunity in Salesforce, I will pre-write the outcome statement before adding capabilities.",
    "When a prospect names a competitor on my next 5 calls, I will name our differentiator before they finish framing.",
    "When my Tuesday demo ends, I will log 2 proof points against the top competitor in the deal record.",
    "When pipeline review starts on Monday, I will state the EB name + budget question for my top 3 deals.",
    "When my next discovery call ends, I will write the dollar quantification of pain in the deal record.",
    "When a prospect asks 'what makes you different?', I will lead with our unique technical proof point, not features.",
    "When I open a new opportunity in Salesforce, I will fill in the EB and DC fields before changing stage.",
]


def pre_responses(session_uuid: str, behavior_ids: list[str]) -> list[AssessmentResponse]:
    out: list[AssessmentResponse] = []
    for i, (lid, lname) in enumerate(LEARNERS):
        out.append(AssessmentResponse(
            session_uuid=session_uuid,
            learner_id=lid,
            learner_name=lname,
            kind="pre",
            frequency_answers={
                behavior_ids[0]: _PRE[i][0],
                behavior_ids[1]: _PRE[i][1],
                behavior_ids[2]: _PRE[i][2],
            },
        ))
    return out


def post_responses(session_uuid: str, behavior_ids: list[str]) -> list[AssessmentResponse]:
    out: list[AssessmentResponse] = []
    for i, (lid, lname) in enumerate(LEARNERS):
        out.append(AssessmentResponse(
            session_uuid=session_uuid,
            learner_id=lid,
            learner_name=lname,
            kind="post",
            frequency_answers={
                behavior_ids[0]: _POST[i][0],
                behavior_ids[1]: _POST[i][1],
                behavior_ids[2]: _POST[i][2],
            },
            commitment=_COMMITMENTS[i],
        ))
    return out


def all_responses(session_uuid: str, behavior_ids: list[str]) -> list[AssessmentResponse]:
    return pre_responses(session_uuid, behavior_ids) + post_responses(session_uuid, behavior_ids)


def distribution(responses: list[AssessmentResponse], kind: str, behavior_id: str) -> dict[str, int]:
    """Counts of each frequency bucket for `behavior_id` across responses of this kind."""
    out: dict[str, int] = {}
    for r in responses:
        if r.kind != kind:
            continue
        choice = r.frequency_answers.get(behavior_id)
        if choice is None:
            continue
        out[choice] = out.get(choice, 0) + 1
    return out
