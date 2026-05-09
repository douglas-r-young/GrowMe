"""build_deck composes slides in the right order with QRs in the right spots."""
from growme.assessment.generator import generate_program_assessment_offline
from growme.decks.builder import build_deck
from growme.schemas import (
    AgendaBlock,
    BaseCompanyResearch,
    BehaviorContext,
    BehaviorFindings,
    CitedFact,
    EnrichedContext,
    SessionPlan,
)


def _enriched():
    bc = BehaviorContext(
        behavior_id="pic_pbo_quantify_pain",
        behavior_name="Quantify pain",
        behavior_description="...",
        framework_origin="PIC: PBO",
        research_questions=[],
        findings=BehaviorFindings(
            examples=[CitedFact(text="ex1", source="g2:u", confidence="high")],
            objections=[CitedFact(text="obj1", source="g2:u", confidence="high")],
            proof_points=[CitedFact(text="proof1", source="g2:u", confidence="high")],
        ),
    )
    return EnrichedContext(
        base=BaseCompanyResearch(company_snapshot="snap"),
        per_behavior=[bc, bc, bc],
        sources_used=["g2:u"],
        research_timestamp="2026-05-09T00:00:00Z",
    )


def _plan():
    return SessionPlan(
        session_number=1,
        title="Photon DB · PIC Mastery",
        behavior_id=None,
        learning_objective="Synthesize all three PIC behaviors in a deal motion.",
        agenda=[AgendaBlock(name=n, duration_min=d, description="...")
                for n, d in [("Open", 5), ("Teach", 15), ("Discuss", 15),
                             ("Practice", 15), ("Close", 10)]],
    )


def test_build_deck_has_pre_qr_and_post_qr_slides_in_order():
    ec = _enriched()
    plan = _plan()
    assessment = generate_program_assessment_offline(
        ["pic_pbo_quantify_pain", "pic_rc_capabilities_outcomes", "pic_diff_differentiate"]
    )
    deck = build_deck(
        plan=plan,
        enriched=ec,
        assessment=assessment,
        pre_qr_url="http://localhost:8501/?assessment=u&kind=pre",
        post_qr_url="http://localhost:8501/?assessment=u&kind=post",
        slide_bodies=[("Quantify pain", "body"), ("Capabilities → outcomes", "body"),
                      ("Differentiate", "body"), ("Integration", "body")],
        facilitator_guide_md="# Guide",
    )
    kinds = [s.kind for s in deck.slides]
    assert kinds[0] == "title"
    assert "poll_qr" in kinds[:3]                    # pre QR appears near start
    assert "poll_qr" in kinds[-3:]                   # post QR appears near end
    assert kinds[-1] == "close"
    pre_qr = next(s for s in deck.slides if s.kind == "poll_qr" and s.qr_url and "kind=pre" in s.qr_url)
    post_qr = next(s for s in deck.slides if s.kind == "poll_qr" and s.qr_url and "kind=post" in s.qr_url)
    assert pre_qr is not None and post_qr is not None
    assert len(pre_qr.body_md) <= 120
    assert len(post_qr.body_md) <= 120
    assert pre_qr.body_md  # non-empty
    assert post_qr.body_md
    assert deck.pre_qr_url == "http://localhost:8501/?assessment=u&kind=pre"
    assert deck.post_qr_url == "http://localhost:8501/?assessment=u&kind=post"
    assert deck.pptx_path is None  # not exported yet
