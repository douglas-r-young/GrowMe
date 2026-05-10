"""One fixed implementation-intention commitment per behavior_id.

Each commitment uses the Gollwitzer "When/Before/After/If/Once <trigger>, I will
<action>" form so it round-trips through ``Commitment.from_string`` and passes
``has_implementation_intention``. Keys match ``behavior_menu.BEHAVIOR_MENU``.
"""
from __future__ import annotations

BEHAVIOR_COMMITMENTS: dict[str, str] = {
    "pic_pbo_quantify_pain": (
        "When a prospect describes a problem on a discovery call, "
        "I will ask 'how do you measure that today?' before moving on."
    ),
    "pic_rc_capabilities_outcomes": (
        "Before naming a product capability in a demo, "
        "I will state the customer outcome it serves."
    ),
    "pic_diff_differentiate": (
        "When a prospect names a competitor, "
        "I will offer one specific proof point instead of a feature comparison."
    ),
    "meddpicc_eb_engage_buyer": (
        "After a positive technical evaluation call, "
        "I will ask my champion for a 20-minute intro to the economic buyer."
    ),
    "meddpicc_dc_decision_criteria": (
        "Before responding to a buyer's evaluation criteria, "
        "I will propose one criterion they have not listed."
    ),
    "universal_price_as_roi": (
        "When a prospect says 'too expensive', "
        "I will re-anchor on payback period before discussing list price."
    ),
}


def commitment_for(behavior_id: str) -> str:
    """Return the fixed commitment for a behavior, or a safe fallback."""
    return BEHAVIOR_COMMITMENTS.get(
        behavior_id,
        "When the moment to practice this behavior arrives, I will pause and try the new approach.",
    )
