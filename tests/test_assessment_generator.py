"""The assessment generator returns 3 frequency questions (one per behavior_id) + 4-5 commitment options."""
from growme.assessment.generator import generate_program_assessment_offline


def test_offline_generator_returns_three_questions_aligned_to_behaviors():
    bids = ["pic_pbo_quantify_pain", "pic_rc_capabilities_outcomes", "pic_diff_differentiate"]
    a = generate_program_assessment_offline(bids)
    assert [q.behavior_id for q in a.pre_questions] == bids
    assert 4 <= len(a.commitment_options) <= 5
    for q in a.pre_questions:
        assert "Often" in q.options
