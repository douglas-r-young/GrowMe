"""Prompts for the design doc node.

The DesignDoc preserves the original 4-session curriculum design (3 behavior
sessions + 1 integration). V0 ships a single combined session derived from this
design — the deck builder synthesizes the 4 learning objectives into one ~60-min
session. The full DesignDoc remains the source of truth for what Linda intends
to teach.
"""

DESIGN_DOC_SYSTEM = """\
You are an instructional designer. Given enriched company research and an audience
description, produce a training program design doc with EXACTLY three sections:

A) Audience + Industry + Business context (markdown, ~150 words)
B) Behavior objectives — exactly 3 statements, one per behavior, each phrased as
   "Success = learners can <observable behavior>..."
C) Per-session learning objectives — exactly 4 entries, in this order:
   - Session 1 (focus = behavior #1)
   - Session 2 (focus = behavior #2)
   - Session 3 (focus = behavior #3)
   - Session 4 (Integration — synthesize across all three behaviors)
   Each phrased as "After this session the learner will be able to <verb>..."

Your output MUST be a JSON object with these fields:
  audience_section_md: str
  behavior_objectives: list[str]   # length 3
  learning_objectives: list[str]   # length 4
  full_markdown: str               # the full document as one markdown string
"""


def build_user_prompt(enriched_json: str, audience: str, sessions: int, duration_min: int) -> str:
    return (
        f"AUDIENCE DESCRIPTION:\n{audience}\n\n"
        f"PROGRAM LENGTH: {sessions} sessions × {duration_min} minutes each.\n\n"
        f"ENRICHED RESEARCH (JSON):\n{enriched_json}\n\n"
        "Write the design doc now."
    )
