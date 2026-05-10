"""Compute pre/post movement per behavior; ask an LLM for the narrative."""
from __future__ import annotations

from pydantic import BaseModel

from growme.assessment.fixtures import distribution
from growme.llm_clients import complete_json
from growme.schemas import (
    AssessmentResponse,
    BehaviorMovement,
    CitedFact,
    DeltaReport,
    EnrichedContext,
)


class _DeltaReasoning(BaseModel):
    top_objection_still_surfacing_text: str
    top_objection_source: str = ""
    recommended_reinforcement_md: str
    summary_md: str


DELTA_SYSTEM = """\
You are an L&D analyst. Given pre/post poll distributions per behavior and a list
of behavior findings (especially objections + proof_points), return:
  - top_objection_still_surfacing_text: the single most likely objection that learners
    will still face given the residual 'rarely/sometimes' counts
  - top_objection_source: a URL from the provided findings if one applies, else ""
  - recommended_reinforcement_md: 2-4 bullets recommending follow-up reinforcement,
    grounded in the proof_points provided
  - summary_md: a 200-word executive summary suitable for the program's L&D lead

Output strict JSON.
"""


def _movements(
    responses: list[AssessmentResponse], behavior_ids: list[str]
) -> list[BehaviorMovement]:
    out: list[BehaviorMovement] = []
    for bid in behavior_ids:
        pre = distribution(responses, "pre", bid)
        post = distribution(responses, "post", bid)
        pre_often = pre.get("Often", 0) + pre.get("Always", 0)
        post_often = post.get("Often", 0) + post.get("Always", 0)
        n = sum(pre.values()) or 1
        pct = (post_often - pre_often) / n
        out.append(BehaviorMovement(
            behavior_id=bid,
            pct_moved_from_rarely_to_often=round(pct, 3),
            pre_distribution=pre,
            post_distribution=post,
        ))
    return out


def run(
    responses: list[AssessmentResponse],
    enriched: EnrichedContext,
) -> DeltaReport:
    behavior_ids = [bc.behavior_id for bc in enriched.per_behavior]
    movements = _movements(responses, behavior_ids)

    findings_blob = "\n\n".join(
        f"### {bc.behavior_name}\nObjections:\n"
        + "\n".join(f"- {f.text} (src={f.source})" for f in bc.findings.objections[:5])
        + "\nProof points:\n"
        + "\n".join(f"- {f.text} (src={f.source})" for f in bc.findings.proof_points[:5])
        for bc in enriched.per_behavior
    )
    pre_post_blob = "\n".join(
        f"{m.behavior_id}: pre={m.pre_distribution}, post={m.post_distribution}, "
        f"pct moved={m.pct_moved_from_rarely_to_often:+.0%}"
        for m in movements
    )

    reasoning = complete_json(
        role="delta_report",
        system=DELTA_SYSTEM,
        user=f"PRE/POST DISTRIBUTIONS:\n{pre_post_blob}\n\nFINDINGS:\n{findings_blob}",
        schema=_DeltaReasoning,
        max_tokens=2000,
    )

    full_md = (
        f"# Behavior Delta Report\n\n"
        f"## Movements\n\n"
        + "\n".join(
            f"- **{m.behavior_id}**: {m.pct_moved_from_rarely_to_often:+.0%} moved into Often+\n"
            f"  - pre: {m.pre_distribution}\n  - post: {m.post_distribution}"
            for m in movements
        )
        + f"\n\n## Top objection still surfacing\n\n"
        f"_{reasoning.top_objection_still_surfacing_text}_\n\n"
        f"## Recommended reinforcement\n\n{reasoning.recommended_reinforcement_md}\n\n"
        f"## Summary\n\n{reasoning.summary_md}\n"
    )

    return DeltaReport(
        behavior_movements=movements,
        top_objection_still_surfacing=CitedFact(
            text=reasoning.top_objection_still_surfacing_text,
            source=(reasoning.top_objection_source or "inference:delta_report"),
            confidence="medium" if reasoning.top_objection_source else "low",
        ),
        recommended_reinforcement_md=reasoning.recommended_reinforcement_md,
        full_markdown=full_md,
    )


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    from growme.assessment.fixtures import all_responses
    from growme.research.node import run as run_research
    from growme.schemas import WizardInputs
    inputs = WizardInputs(
        company_url="neon.tech", company_alias="Photon DB",
        audience_description="12 mid-market AEs",
        selected_behavior_ids=[
            "pic_pbo_quantify_pain",
            "pic_rc_capabilities_outcomes",
            "pic_diff_differentiate",
        ],
    )
    ec = run_research(inputs)
    rs = all_responses("smoke", inputs.selected_behavior_ids)
    report = run(rs, ec)
    print(report.full_markdown)
