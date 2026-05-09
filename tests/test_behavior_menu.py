"""The 6-behavior menu must have exactly 6 entries with templated questions."""
from growme.behavior_menu import BEHAVIOR_MENU, default_pic_behavior_ids


def test_menu_has_six_entries():
    assert len(BEHAVIOR_MENU) == 6


def test_pic_defaults_present():
    for bid in default_pic_behavior_ids():
        assert bid in BEHAVIOR_MENU


def test_every_template_has_four_questions_with_company_slot():
    for tmpl in BEHAVIOR_MENU.values():
        rq = tmpl.research_questions
        for q in (rq.examples, rq.baselines, rq.objections, rq.proof_points):
            assert "{company}" in q, f"Missing {{company}} slot in {tmpl.id}"


def test_default_pic_count_is_three():
    assert len(default_pic_behavior_ids()) == 3
