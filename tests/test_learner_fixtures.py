"""Tests for the 8-learner pre/post assessment fixtures."""
from growme.assessment.fixtures import all_responses, distribution, post_responses, pre_responses


_BIDS = ["b1", "b2", "b3"]
_SESSION = "u"


def test_pre_responses_count_and_kind():
    responses = pre_responses(_SESSION, _BIDS)
    assert len(responses) == 8
    for r in responses:
        assert r.kind == "pre"
        for bid in _BIDS:
            assert bid in r.frequency_answers


def test_post_responses_count_kind_and_commitment():
    responses = post_responses(_SESSION, _BIDS)
    assert len(responses) == 8
    for r in responses:
        assert r.kind == "post"
        assert r.commitment is not None


def test_distribution_total_equals_learner_count():
    responses = all_responses(_SESSION, _BIDS)
    dist = distribution(responses, "pre", "b1")
    assert sum(dist.values()) == 8


def test_b1_lift_post_exceeds_pre():
    responses = all_responses(_SESSION, _BIDS)
    high_freq = {"Often", "Always"}
    pre_high = sum(
        1 for r in responses
        if r.kind == "pre" and r.frequency_answers.get("b1") in high_freq
    )
    post_high = sum(
        1 for r in responses
        if r.kind == "post" and r.frequency_answers.get("b1") in high_freq
    )
    assert post_high > pre_high
