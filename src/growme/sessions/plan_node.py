"""Generate ONE SessionPlan covering all three selected behaviors.

V0 demo simplification: the program collapses to a single ~60-min session that
follows the integration-session pattern from the original spec — multi-behavior
scenario, switching between behaviors in the role-play, cross-cutting commitment.
"""
from __future__ import annotations

from growme.llm_clients import complete_json
from growme.schemas import (
    AgendaBlock,
    BehaviorContext,
    EnrichedContext,
    SessionPlan,
    WizardInputs,
)

SESSION_PLAN_SYSTEM = """\
You are an instructional designer. Generate ONE SessionPlan (~60 min) that
covers all three behaviors in a single integration session.

The session has:
  session_number: 1
  title: short, demo-readable (mentions all three behaviors implicitly)
  behavior_id: null  (this is the integration session, not behavior-specific)
  learning_objective: "After this session the learner will be able to <verb>..."
    The verb should reflect synthesizing across all three behaviors.
  agenda: a list of AgendaBlocks summing to ~60 minutes:
    Opening hook (5)  | Teach (15)  | Discuss (15)  | Practice/role-play (15)  | Commitment + close (10)
  Each AgendaBlock has: name, duration_min, description (1-2 sentences).

Ground the role-play in a multi-behavior scenario sourced from the per-behavior
findings — set up uses .examples, tension uses .objections, recovery uses
.proof_points. The opening hook should anchor on the connection between the
three behaviors.

Output strict JSON: a single SessionPlan object.
"""


def run(
    design_doc_md: str,
    enriched: EnrichedContext,
    inputs: WizardInputs,
) -> SessionPlan:
    behavior_blocks = "\n\n".join(
        _format_behavior_block(bc) for bc in enriched.per_behavior
    )
    user = (
        f"DESIGN DOC (Linda's edited version):\n{design_doc_md}\n\n"
        f"BEHAVIOR ORDER:\n"
        f"  1: {inputs.selected_behavior_ids[0]}\n"
        f"  2: {inputs.selected_behavior_ids[1]}\n"
        f"  3: {inputs.selected_behavior_ids[2]}\n\n"
        f"PER-BEHAVIOR FINDINGS:\n{behavior_blocks}\n"
    )
    plan = complete_json(
        role="session_plan",
        system=SESSION_PLAN_SYSTEM,
        user=user,
        schema=SessionPlan,
        max_tokens=2000,
    )
    if plan.behavior_id is not None:
        # Force null — V0 has no per-behavior session.
        plan = plan.model_copy(update={"behavior_id": None})
    if plan.session_number != 1:
        plan = plan.model_copy(update={"session_number": 1})
    return plan


def _format_behavior_block(bc: BehaviorContext) -> str:
    examples = "\n".join(f"- {f.text}" for f in bc.findings.examples[:3])
    objections = "\n".join(f"- {f.text}" for f in bc.findings.objections[:3])
    return (
        f"### {bc.behavior_name}  ({bc.framework_origin})\n"
        f"Examples:\n{examples}\nObjections:\n{objections}"
    )


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    from growme.research.node import run as run_research
    from growme.design_doc.node import run as run_design_doc
    inputs = WizardInputs(
        company_url="neon.tech",
        company_alias="Photon DB",
        audience_description="12 mid-market AEs",
        selected_behavior_ids=[
            "pic_pbo_quantify_pain",
            "pic_rc_capabilities_outcomes",
            "pic_diff_differentiate",
        ],
    )
    ec = run_research(inputs)
    doc = run_design_doc(ec, inputs)
    plan = run(doc.full_markdown, ec, inputs)
    print(f"=== Session {plan.session_number}: {plan.title} ===")
    print(f"  obj: {plan.learning_objective}")
    for ab in plan.agenda:
        print(f"   • {ab.name} ({ab.duration_min}m): {ab.description[:80]}")
