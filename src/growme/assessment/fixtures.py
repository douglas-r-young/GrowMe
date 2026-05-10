# src/growme/assessment/fixtures.py
"""8 simulated learners with one pre + one post AssessmentResponse each.

Pre answers skew Rarely/Sometimes; post answers skew Sometimes/Often with
non-uniform movement so the delta has narrative depth (one behavior shifts
more than the other two).
"""
from __future__ import annotations

from growme.schemas import AssessmentResponse

LEARNERS = [
    ("learner_01", "Sam Patel"),
    ("learner_02", "Riya Chen"),
    ("learner_03", "Marcus Vega"),
    ("learner_04", "Tasha Brooks"),
    ("learner_05", "Jordan Kim"),
    ("learner_06", "Priya Nair"),
    ("learner_07", "Diego Souza"),
    ("learner_08", "Lena Park"),
]

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
_COMMITMENTS = [
    "On 3 calls this week, ask 'how do you measure that today?'",
    "Pre-write outcome statements for top 3 capabilities I pitch",
    "Always name the competitor first in next 5 calls",
    "Memorize 2 proof points per top competitor",
    "On 3 calls this week, ask 'how do you measure that today?'",
    "Pre-write outcome statements for top 3 capabilities I pitch",
    "Always name the competitor first in next 5 calls",
    "On 3 calls this week, ask 'how do you measure that today?'",
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
