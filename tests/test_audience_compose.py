from growme.app import audience_compose


def test_compose_audience_description_joins_sections() -> None:
    out = audience_compose.compose_audience_description(
        target_audience="Enterprise AEs",
        cohort_size="10–20 participants",
        program_format="Single session (demo)",
        notes="Focus on practical drills.",
    )
    assert "Target audience: Enterprise AEs" in out
    assert "Cohort size: 10–20 participants" in out
    assert "Program format: Single session (demo)" in out
    assert "Focus on practical drills." in out


def test_compose_omits_blank_notes() -> None:
    out = audience_compose.compose_audience_description(
        target_audience="SDRs / BDRs",
        cohort_size="1–9 participants",
        program_format="Half day",
        notes="   \n  ",
    )
    assert out.count("\n") == 2
    assert "SDRs" in out
