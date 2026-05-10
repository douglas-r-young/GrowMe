"""Open the produced .pptx in Keynote / PowerPoint to eyeball."""
from pathlib import Path
from growme.assessment.generator import generate_program_assessment_offline
from growme.decks.builder import build_deck
from growme.decks.pptx import export_pptx
from growme.schemas import (
    AgendaBlock, BaseCompanyResearch, BehaviorContext, BehaviorFindings,
    CitedFact, EnrichedContext, SessionPlan,
)
bc = BehaviorContext(behavior_id="a", behavior_name="x", behavior_description="x",
                    framework_origin="PIC", research_questions=[],
                    findings=BehaviorFindings())
ec = EnrichedContext(base=BaseCompanyResearch(company_snapshot="..."),
                     per_behavior=[bc, bc, bc], sources_used=[],
                     research_timestamp="2026-05-09T00:00:00Z")
plan = SessionPlan(session_number=1, title="Smoke deck", behavior_id=None,
                   learning_objective="t",
                   agenda=[AgendaBlock(name="x", duration_min=5, description="x")])
assessment = generate_program_assessment_offline(
    ["pic_pbo_quantify_pain", "pic_rc_capabilities_outcomes", "pic_diff_differentiate"]
)
deck = build_deck(plan=plan, enriched=ec, assessment=assessment,
                  pre_qr_url="http://localhost:8501/?assessment=u&kind=pre",
                  post_qr_url="http://localhost:8501/?assessment=u&kind=post",
                  slide_bodies=[("B1","x"),("B2","x"),("B3","x"),("Int","x")],
                  facilitator_guide_md="# guide")
out = export_pptx(deck, Path("/tmp/growme_smoke.pptx"))
print(f"wrote {out}")
