"""Schema-level test that DeckPlan accepts the planner output shape."""
from growme.decks.llm import DeckPlan, PlannedSlide


def test_deckplan_accepts_18_slide_skeleton():
    slides = [
        PlannedSlide(layout="cover",
                     blocks={"eyebrow": "GrowMe", "title": "T", "subtitle": "s",
                             "image_prompt": "abstract"},
                     speaker_notes="x" * 100),
        PlannedSlide(layout="poll_qr", blocks={}, speaker_notes="x" * 100),
        PlannedSlide(layout="teach",
                     blocks={"eyebrow": "Why", "title": "Why",
                             "bullets": ["a", "b"], "citation": "src"},
                     speaker_notes="x" * 100),
    ]
    for i in range(3):
        slides += [
            PlannedSlide(layout="section_divider",
                         blocks={"number": f"0{i+1}", "behavior_name": "B",
                                 "promise": "p", "image_prompt": "art"},
                         speaker_notes="x" * 100),
            PlannedSlide(layout="teach",
                         blocks={"eyebrow": "F", "title": "T",
                                 "bullets": ["a", "b", "c"], "citation": ""},
                         speaker_notes="x" * 100),
            PlannedSlide(layout="example",
                         blocks={"title": "E",
                                 "before_body": "before", "after_body": "after"},
                         speaker_notes="x" * 100),
            PlannedSlide(layout="activity",
                         blocks={"eyebrow": "Try", "title": "A",
                                 "prompt": "p", "sub_prompts": ["x"], "timer_hint": "5"},
                         speaker_notes="x" * 100),
        ]
    slides += [
        PlannedSlide(layout="activity",
                     blocks={"eyebrow": "Integration", "title": "I",
                             "prompt": "p", "sub_prompts": ["x"], "timer_hint": "10"},
                     speaker_notes="x" * 100),
        PlannedSlide(layout="poll_qr", blocks={}, speaker_notes="x" * 100),
        PlannedSlide(layout="close",
                     blocks={"title": "Thanks", "commitment_recap": "c", "next_step": "n"},
                     speaker_notes="x" * 100),
    ]
    dp = DeckPlan(slides=slides)
    assert len(dp.slides) == 18
    assert dp.slides[0].layout == "cover"
    assert dp.slides[-1].layout == "close"


def test_planner_speaker_notes_min_length_enforced():
    import pytest
    with pytest.raises(Exception):
        PlannedSlide(layout="teach", blocks={}, speaker_notes="too short")


def test_activity_prompt_rejects_overlong():
    import pytest

    from growme.decks.llm import ActivityBlocks

    # 180 is the cap; 181 must fail.
    with pytest.raises(Exception):
        ActivityBlocks(
            eyebrow="Try it · 5 min",
            title="A",
            prompt="x" * 181,
            sub_prompts=["a"],
            timer_hint="5 min",
        )


def test_activity_sub_prompt_item_rejects_overlong():
    import pytest

    from growme.decks.llm import ActivityBlocks

    with pytest.raises(Exception):
        ActivityBlocks(
            eyebrow="Try it · 5 min",
            title="A",
            prompt="ok",
            sub_prompts=["x" * 101],   # per-item cap is 100
            timer_hint="5 min",
        )


def test_close_recap_and_next_step_reject_overlong():
    import pytest

    from growme.decks.llm import CloseBlocks

    with pytest.raises(Exception):
        CloseBlocks(title="Thanks", commitment_recap="x" * 181, next_step="ok")
    with pytest.raises(Exception):
        CloseBlocks(title="Thanks", commitment_recap="ok ok ok ok", next_step="x" * 181)


def test_example_body_reject_overlong():
    import pytest

    from growme.decks.llm import ExampleBlocks

    with pytest.raises(Exception):
        ExampleBlocks(
            title="E",
            before_body="x" * 261,
            after_body="ok ok ok ok",
        )
