"""Unit tests for _movements — pure logic, no LLM calls."""
from growme.delta_report.node import _movements
from growme.schemas import AssessmentResponse


def test_movements_builds_per_behavior_distributions():
    responses = [
        AssessmentResponse(session_uuid="u", learner_id="l1", learner_name="L", kind="pre",  frequency_answers={"b1": "Rarely"}),
        AssessmentResponse(session_uuid="u", learner_id="l2", learner_name="L", kind="pre",  frequency_answers={"b1": "Often"}),
        AssessmentResponse(session_uuid="u", learner_id="l3", learner_name="L", kind="post", frequency_answers={"b1": "Often"}),
        AssessmentResponse(session_uuid="u", learner_id="l4", learner_name="L", kind="post", frequency_answers={"b1": "Always"}),
    ]
    result = _movements(responses, ["b1"])
    assert len(result) == 1
    m = result[0]
    assert m.behavior_id == "b1"
    assert m.pre_distribution == {"Rarely": 1, "Often": 1}
    assert m.post_distribution == {"Often": 1, "Always": 1}
    assert m.pct_moved_from_rarely_to_often == 0.5


def test_movements_empty_responses_no_division_by_zero():
    result = _movements([], ["b1"])
    assert len(result) == 1
    m = result[0]
    assert m.pre_distribution == {}
    assert m.post_distribution == {}
    assert m.pct_moved_from_rarely_to_often == 0.0
