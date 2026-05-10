"""Generate the program-level pre/post assessment.

Online path: LLM (Featherless cheap) writes a behavior-specific frequency prompt
+ 4-5 demo-grounded commitment options.

Offline path: deterministic fallback that pulls behavior names from BEHAVIOR_MENU.
Used by tests and by the no-LLM dry-run path in scripts/e2e_dry_run.py.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from growme.behavior_menu import BEHAVIOR_MENU
from growme.llm_clients import complete_json
from growme.pedagogy import ASSESSMENT_PRINCIPLES
from growme.schemas import (
    EnrichedContext,
    FrequencyQuestion,
    ProgramAssessment,
    WizardInputs,
)


class _LLMOut(BaseModel):
    pre_question_prompts: list[str] = Field(min_length=3, max_length=3)
    commitment_options: list[str] = Field(min_length=4, max_length=5)


ASSESSMENT_SYSTEM = f"""\
You write a short pre/post assessment for a sales-skills training program.

Inputs: three behaviors (name + description) and a list of supporting proof
points sourced from real customer/company research.

Output strict JSON with exactly two fields:
  pre_question_prompts: list of 3 strings, one per behavior. Each string is a
    single-sentence frequency question phrased in plain English about how often
    the rep does the behavior in their typical week ("How often do you …?").
    Do NOT include answer options — those are appended downstream.
  commitment_options: list of 4-5 short, concrete actions a rep could pledge to
    take in the next 7 days. Each MUST use "When [trigger], I will [action]" form
    (Gollwitzer implementation intentions). Ground each in the proof points where
    possible.

{ASSESSMENT_PRINCIPLES}
"""


def generate_program_assessment(
    enriched: EnrichedContext,
    inputs: WizardInputs,
) -> ProgramAssessment:
    """LLM-backed generator. Calls Featherless via role='nudges' (cheap)."""
    behavior_blob = "\n\n".join(
        f"### {bc.behavior_name}\n{bc.behavior_description}\n"
        f"Proof points:\n" + "\n".join(f"- {f.text}" for f in bc.findings.proof_points[:3])
        for bc in enriched.per_behavior
    )
    user = (
        f"BEHAVIORS (in order):\n{behavior_blob}\n\n"
        f"AUDIENCE: {inputs.audience_description}\n"
    )
    out = complete_json(
        role="nudges",
        system=ASSESSMENT_SYSTEM,
        user=user,
        schema=_LLMOut,
        max_tokens=1200,
    )
    return ProgramAssessment(
        pre_questions=[
            FrequencyQuestion(behavior_id=bid, prompt=prompt)
            for bid, prompt in zip(inputs.selected_behavior_ids, out.pre_question_prompts, strict=True)
        ],
        commitment_options=out.commitment_options,
    )


def generate_program_assessment_offline(behavior_ids: list[str]) -> ProgramAssessment:
    """Deterministic fallback. Used by tests and offline dry-runs."""
    questions = [
        FrequencyQuestion(
            behavior_id=bid,
            prompt=f"How often do you {BEHAVIOR_MENU[bid].name.lower().rstrip('.')}?",
        )
        for bid in behavior_ids
    ]
    return ProgramAssessment(
        pre_questions=questions,
        commitment_options=[
            "When my next discovery call starts, I will ask 'how do you measure that today?' before any capability pitch.",
            "When I open a new opportunity in Salesforce, I will pre-write the outcome statement before adding the next capability.",
            "When a prospect mentions a competitor on my next 5 calls, I will name our differentiator before they finish framing.",
            "When my Tuesday demo ends, I will log 2 proof points against the top competitor in the deal record.",
        ],
    )


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    from growme.research.node import run as run_research
    inp = WizardInputs(
        company_url="neon.tech",
        company_alias="Photon DB",
        audience_description="12 mid-market AEs",
        selected_behavior_ids=[
            "pic_pbo_quantify_pain",
            "pic_rc_capabilities_outcomes",
            "pic_diff_differentiate",
        ],
    )
    ec = run_research(inp)
    a = generate_program_assessment(ec, inp)
    print(a.model_dump_json(indent=2))
