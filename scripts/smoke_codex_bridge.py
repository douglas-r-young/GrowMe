"""Live smoke test: emit a one-frame, one-text plan; invoke codex exec; print result."""
import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from growme.miro.intent import MiroFrame, MiroPlan, MiroSlide, write_plan  # noqa: E402
from growme.miro.codex_bridge import apply_plan  # noqa: E402


plan = MiroPlan(
    board_id=os.environ["MIRO_BOARD_ID"],
    build_step="materials",
    frames=[MiroFrame(key="smoke_frame", title="GrowMe codex smoke", x=0, y=0,
                       width=600, height=400)],
    slides=[MiroSlide(key="smoke_frame.text_0", parent_key="smoke_frame",
                       title="Hello", body_md="Hello from GrowMe smoke test",
                       x=-200, y=0, width=400)],
)

with tempfile.TemporaryDirectory() as d:
    path = write_plan(plan, Path(d) / "smoke_plan.json")
    result = apply_plan(path, board_id=os.environ["MIRO_BOARD_ID"], timeout=120)
    print(f"status={result.status}")
    print(f"exit_code={result.exit_code}")
    print(f"item_ids={result.item_ids}")
    if result.status == "error":
        print("STDERR:")
        print(result.stderr)
