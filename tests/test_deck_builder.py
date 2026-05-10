"""build_deck composes slides from a DeckPlan with QR slides in the right spots."""
from growme.decks.builder import build_deck, collect_image_prompts
from growme.decks.llm import DeckPlan, PlannedSlide
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


def _planned(layout, blocks):
    return PlannedSlide(layout=layout, blocks=blocks, speaker_notes="x" * 100)


def _deck_plan() -> DeckPlan:
    """Mirrors STORY_ARC_SKELETON: cover, pre-qr, why, then 3×{div,teach,ex,act}, integration, post-qr, close."""
    slides = [
        _planned("cover", {"eyebrow": "GrowMe", "title": "Photon DB · PIC", "subtitle": "lo", "image_prompt": "abstract"}),
        _planned("poll_qr", {}),
        _planned("teach", {"eyebrow": "Why", "title": "Why this session", "bullets": ["a", "b"], "citation": "src"}),
    ]
    for i, name in enumerate(["Quantify pain", "Capabilities → outcomes", "Differentiate"], start=1):
        slides.append(_planned("section_divider", {"number": f"0{i}", "behavior_name": name, "promise": "p", "image_prompt": f"art {i}"}))
        slides.append(_planned("teach", {"eyebrow": "SPIN", "title": name, "bullets": ["a", "b", "c"], "citation": "src"}))
        slides.append(_planned("example", {"title": "Ex", "before_body": "before text", "after_body": "after text"}))
        slides.append(_planned("activity", {"eyebrow": "Try it · 5 min", "title": "Activity", "prompt": "do this", "sub_prompts": ["x", "y"], "timer_hint": "5 min"}))
    slides.append(_planned("activity", {"eyebrow": "Integration", "title": "Combine all three", "prompt": "role-play", "sub_prompts": ["a"], "timer_hint": "10 min"}))
    slides.append(_planned("poll_qr", {}))
    slides.append(_planned("close", {"title": "Thanks", "commitment_recap": "you committed", "next_step": "nudge next week"}))
    return DeckPlan(slides=slides)


def test_build_deck_composes_planned_slides_and_overrides_qr_urls():
    ec = _enriched()
    plan = _plan()
    dp = _deck_plan()

    deck = build_deck(
        plan=plan,
        enriched=ec,
        deck_plan=dp,
        pre_qr_url="http://localhost:8501/?assessment=u&kind=pre",
        post_qr_url="http://localhost:8501/?assessment=u&kind=post",
        facilitator_guide_md="# Guide",
        image_paths=[None, None, None, None],  # cover + 3 dividers
    )

    layouts = [s.layout for s in deck.slides]
    assert layouts[0] == "cover"
    assert layouts[1] == "poll_qr"
    assert layouts[-1] == "close"
    assert layouts[-2] == "poll_qr"

    pre_qr = next(s for s in deck.slides if s.layout == "poll_qr" and "kind=pre" in (s.qr_url or ""))
    post_qr = next(s for s in deck.slides if s.layout == "poll_qr" and "kind=post" in (s.qr_url or ""))
    assert pre_qr.qr_caption and post_qr.qr_caption
    assert pre_qr.body_md and post_qr.body_md
    assert deck.pre_qr_url.endswith("kind=pre")
    assert deck.post_qr_url.endswith("kind=post")
    assert deck.pptx_path is None

    # Every non-QR slide must carry speaker notes from the planner.
    for s in deck.slides:
        if s.layout != "poll_qr":
            assert len(s.speaker_notes) >= 80


def test_collect_image_prompts_returns_cover_plus_dividers_in_order():
    dp = _deck_plan()
    prompts = collect_image_prompts(dp)
    assert len(prompts) == 4  # cover + 3 section_dividers
    assert prompts[0] == "abstract"
    assert prompts[1] == "art 1"
    assert prompts[3] == "art 3"
