"""Build audience_description for WizardInputs from structured UI fields."""

from __future__ import annotations


def compose_audience_description(
    *,
    target_audience: str,
    cohort_size: str,
    program_format: str,
    notes: str,
) -> str:
    lines = [
        f"Target audience: {target_audience}",
        f"Cohort size: {cohort_size}",
        f"Program format: {program_format}",
    ]
    notes = notes.strip()
    if notes:
        lines.append("")
        lines.append(notes)
    return "\n".join(lines)
