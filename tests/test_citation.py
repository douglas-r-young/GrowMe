from growme.research.citation import cited_fact, source_g2, source_web, source_wizard


def test_source_helpers_format_correctly():
    assert source_g2("https://www.g2.com/products/neon").startswith("g2:")
    assert source_web("https://example.com").startswith("web:")
    assert source_wizard("audience_description").startswith("wizard:")


def test_cited_fact_high_confidence_when_explicit_url():
    cf = cited_fact("text here", source_g2("https://www.g2.com/products/neon"))
    assert cf.confidence == "high"


def test_cited_fact_low_confidence_for_inferred():
    cf = cited_fact("inferred text", "inference:llm", confidence="low")
    assert cf.confidence == "low"
    assert cited_fact("x", "inference:llm").confidence == "medium"
