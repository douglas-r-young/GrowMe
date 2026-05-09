"""The 6-behavior menu must have exactly 6 entries with templated questions."""
from growme.behavior_menu import BEHAVIOR_MENU, default_pic_behavior_ids, render_questions_for_company


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


def test_render_questions_substitutes_company_and_preserves_order():
    qs = render_questions_for_company("pic_pbo_quantify_pain", "Photon DB")
    assert len(qs) == 4
    assert all("Photon DB" in q for q in qs)
    assert all("{company}" not in q for q in qs)
    tmpl = BEHAVIOR_MENU["pic_pbo_quantify_pain"]
    assert qs[0] == tmpl.research_questions.examples.format(company="Photon DB")
    assert qs[1] == tmpl.research_questions.baselines.format(company="Photon DB")
    assert qs[2] == tmpl.research_questions.objections.format(company="Photon DB")
    assert qs[3] == tmpl.research_questions.proof_points.format(company="Photon DB")


def test_each_entry_id_matches_its_dict_key():
    for key, tmpl in BEHAVIOR_MENU.items():
        assert key == tmpl.id, f"key {key} != id {tmpl.id}"
