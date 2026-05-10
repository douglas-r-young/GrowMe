"""Generate ONE SessionPlan covering all three selected behaviors.

V0 ships a single ~60-min integration session — multi-behavior scenario, switching
between behaviors in the role-play, cross-cutting commitment.

The SESSION_PLAN_SYSTEM concatenates SESSION_PLAN_PRINCIPLES from the pedagogy
package — that bundle carries pacing rules, block floors, bucket ratios,
human-handoff markers.
"""
from __future__ import annotations

from growme.llm_clients import complete_json
from growme.pedagogy import SESSION_PLAN_PRINCIPLES
from growme.schemas import (
    AgendaBlock,
    BehaviorContext,
    EnrichedContext,
    SessionPlan,
    WizardInputs,
)

SESSION_PLAN_SYSTEM = f"""\
You are an instructional designer. Generate ONE SessionPlan (~60 min) that
covers all three behaviors in a single integration session.

The session has:
  session_number: 1
  title: short, demo-readable (mentions all three behaviors implicitly)
  behavior_id: null  (this is the integration session, not behavior-specific)
  learning_objective: "After this session the learner will be able to <verb> when <trigger>..."
    The verb should reflect synthesizing across all three behaviors.
  agenda: a list of AgendaBlocks. Each AgendaBlock has:
    - name: short label
    - duration_min: int
    - description: 1-2 sentences. Tag the bucket in the description like
      "[bucket: framework]" or "[bucket: storytelling]" — the renderer parses this
      and the structural validator enforces ratios.
    - bucket: one of "framework", "story", "activity", "discussion", "buffer".
  Total agenda minutes ∈ [55, 65]. At least one block has bucket="buffer" with
  duration_min ≥ 5.

Ground the role-play in a multi-behavior scenario sourced from the per-behavior
findings — set up uses .examples, tension uses .objections, recovery uses
.proof_points. The opening hook anchors on the connection between the three
behaviors.

{SESSION_PLAN_PRINCIPLES}

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
    proof_points = "\n".join(f"- {f.text}" for f in bc.findings.proof_points[:3])
    return (
        f"### {bc.behavior_name}  ({bc.framework_origin})\n"
        f"Examples:\n{examples}\nObjections:\n{objections}\nProof points:\n{proof_points}"
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
