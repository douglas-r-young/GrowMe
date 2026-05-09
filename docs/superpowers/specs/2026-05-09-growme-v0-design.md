# GrowMe V0 — Design Spec

**Status**: design (pre-implementation)
**Date**: 2026-05-09
**Scope**: Hackathon V0, end-to-end thin slice, solo, ~24 hours
**Demo persona**: Linda, sales manager at "Photon DB" (a disguised Neon)

---

## 1. TL;DR

GrowMe turns a manager's behavior gap into a measurable behavior change. Linda inputs her company, audience, and three behaviors picked from a curated menu. An agentic pipeline researches the company against each behavior, generates an editable design doc, and — on her command — builds a complete training program on a Miro board: four 60-minute sessions of slides, polls, facilitator guides, and post-training nudges. After fast-forwarded simulated learners complete the sessions, GrowMe produces a behavior delta report.

The unique angle is the combination of (a) behavior-conditioned research grounded in real company data, (b) Miro as the artifact canvas, and (c) measurable behavior delta over the full pre/post loop — all from a single intake.

---

## 2. Use case anchor

**Linda** is a sales manager for an inside sales rep team at Photon DB (an alias for Neon — under the hood, our Apify scrapers hit `neon.tech`; the output is `replace_all("Neon", "Photon DB")`). She has noticed her reps don't build quantifiable business cases. She wants a 4-session "Command of the Message" program covering three behaviors:

1. Quantify customer pain in business impact terms (PIC: PBO)
2. Connect product capabilities to required outcomes, not features (PIC: RC)
3. Differentiate from named competitors with credible proof (PIC: Diff)

These three behaviors are pre-checked in the demo's behavior menu.

---

## 3. Architectural shape

### 3.1 Top-level (boxes and arrows)

```
┌──────────────────────────────────────┐   ┌────────────────────┐   ┌────────────────────────────┐
│  STREAMLIT WEB APP                   │   │  CODEX CLI         │   │  MIRO BOARD                │
│  (Linda's home base)                 │   │  + Miro MCP server │   │  (System artifacts canvas) │
├──────────────────────────────────────┤   ├────────────────────┤   ├────────────────────────────┤
│  Wizard Step 1: Company + Audience   │   │  Reads JSON plan   │   │  ⬛ Session 1 frame         │
│  Wizard Step 2: Behavior menu (6→3)  │   │  Iterates items in │   │     • Slides (frames)      │
│  Wizard Step 3: 🪄 Generation        │──▶│   declared order   │──▶│     • Pre/post polls       │
│                  → Design Doc preview│   │  Calls mcp__miro__ │   │     • Facilitator guide    │
│                  → 📝 Editable        │   │   tools per item   │   │  ⬛ Session 2 frame         │
│                  → [BUILD ON MIRO]   │   │  Prints item ids + │   │  ⬛ Session 3 frame         │
│  Wizard Step 4: Build progress       │   │   BUILD COMPLETE   │   │  ⬛ Session 4 frame         │
│  Demo Console: Fast-forward          │──▶│                    │──▶│  ⬛ Nudges frame            │
│                                      │   │                    │   │     • Per-learner email   │
│                                      │   │                    │   │  ⬛ Behavior delta report   │
└──────────────────────────────────────┘   └────────────────────┘   └────────────────────────────┘
       │                                            ▲
       └─ writes .growme_sessions/<uuid>/miro_plan_{materials,nudges,delta}.json
                       └─ invokes `codex exec` (blocking subprocess; see §4.4)
                          USE_LIVE_MIRO=false short-circuits to dry-run (plan only)
```

### 3.2 Three layers

1. **Streamlit shell** — the only UI Linda sees. Multi-step wizard plus a Demo Console page for fast-forwarding simulated time.
2. **LangGraph orchestrator** — six agentic nodes: research (Phase A + B) → design doc → session plan → materials → nudges → delta report.
3. **Miro board** — the system of record for all visible artifacts except the design doc. Materialized via a Codex CLI subprocess that drives a configured Miro MCP server (see §4.4). Python never holds a Miro REST token; the only Miro env var is `MIRO_BOARD_ID`, passed to Codex via the prompt.

### 3.3 Artifact split (where things live)

Editable text (design doc) lives where editing is easy: Streamlit `st.text_area`. Visual artifacts (slides, polls, facilitator guides, nudges, delta report) live where they're consumed: Miro. The [BUILD ON MIRO] button is the boundary.

### 3.4 What we deliberately don't build for V0

- No auth, no multi-tenant; single hardcoded Streamlit session.
- No database; persistence is pickle-on-disk keyed by session UUID.
- No source-document upload (templated research questions cover the need; revisit in V1).
- No real email/Slack send; nudges render as Miro cards. Optional Resend send if time permits.
- No Linda edit on research output; no Linda edit on materials. Single edit point at the design doc.
- No Python-side Miro REST client. All board writes are delegated to a `codex exec` subprocess that calls the configured Miro MCP server's tools.

---

## 4. The LangGraph agentic flow

```
START
  │  Wizard inputs: company_url=neon.tech (alias=Photon DB),
  │  audience_description, selected_behavior_ids[3] from menu of 6
  ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. RESEARCH (2-phase, mostly parallel)                           │
│                                                                  │
│   ┌─ Phase A: Base Company Research (parallel branches) ─────┐   │
│   │  • company_snapshot ← Apify website-content-crawler      │   │
│   │  • customer_voice   ← Apify g2-product-scraper           │   │
│   │  • vertical_vocab   ← LLM extract (Featherless cheap)    │   │
│   │  • named_competitors← Web search + LLM                   │   │
│   └──────────────────────────────────────────────────────────┘   │
│                            ║                                     │
│   ┌─ Phase B: Per-Behavior Research (3× parallel sub-graphs)─┐   │
│   │  For each selected_behavior_id:                          │   │
│   │   1. Load 4 templated questions from BEHAVIOR_MENU       │   │
│   │      (examples, baselines, objections, proof_points)     │   │
│   │   2. Substitute {company} = "Photon DB"                  │   │
│   │   3. Targeted research per question:                     │   │
│   │      • Sub-filter G2 reviews                             │   │
│   │      • Targeted web search                               │   │
│   │      • LLM synthesis → BehaviorFindings bucket           │   │
│   │      • Every fact gets a CitedFact(source, confidence)   │   │
│   │   4. Apply Photon→Neon alias map to outputs              │   │
│   └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│   Out: EnrichedContext { base, per_behavior[3], sources, ts }    │
│   Failure mode: cached fixtures available as fallback            │
│   Target time: <90s                                              │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. DESIGN_DOC                                                    │
│   LLM: Featherless                                               │
│   Inputs: EnrichedContext, audience_description, length=4×60min  │
│   Out: Markdown with three sections:                             │
│     A) Audience + Industry + Business context (from base)        │
│     B) Behavior objectives — 3 statements, one per behavior      │
│        ("Success = learners can <behavior>...")                  │
│     C) Per-session learning objectives × 4                       │
│        (3 behavior sessions + 1 integration session)             │
│   Side effect: render to Streamlit (not Miro)                    │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
╔═════════════════════════════════════════════════════════════════╗
║  HUMAN-IN-THE-LOOP — SINGLE EDIT POINT                           ║
║  Linda reviews + edits design doc in Streamlit text_area,        ║
║  then clicks [BUILD ON MIRO]. Edits override the LLM output      ║
║  in `design_doc_edited_md`.                                      ║
╚═════════════════════════════════════════════════════════════════╝
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. SESSION_PLAN  (LLM: OpenAI gpt-4o — heavy reasoning)          │
│   For each of 4 sessions, generate Agenda:                       │
│     Opening hook (5) → Teach (15) → Discuss (15) →               │
│     Practice/role-play (15) → Commitment + close (10)            │
│   Role-play scenarios pull from BehaviorFindings.examples +      │
│     .objections directly.                                        │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. MATERIALS  (LLM: OpenAI gpt-4o; 4 sessions × 3 parallel = 12)│
│   Per session, in parallel:                                      │
│     a) Slides → MiroFrame + MiroSlide plan fragments             │
│        (slide content draws on .examples + .baselines)           │
│     b) Pre-poll + Post-commitment poll → MiroPoll fragments      │
│        (poll questions templated against .baselines)             │
│     c) Facilitator guide → MiroDoc fragment                      │
│        (objection-handling section pulls .objections)            │
│   Aggregator: Streamlit writes miro_plan_materials.json,         │
│   dispatches codex_bridge.apply_plan(...) — see §4.4.            │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼ (Demo Console: fast-forward "session 1 complete", etc.)
  │   Pre-seeded learner responses replayed into Miro polls
  │
┌─────────────────────────────────────────────────────────────────┐
│ 5. NUDGES  (LLM: Featherless cheap, high volume)                 │
│   Reads commitment poll responses from learner fixtures.         │
│   Generates personalized email + Slack copy per learner,         │
│   keyed to their commitment + relevant .proof_points.            │
│   Output: MiroCard fragments (one per learner per session).      │
│   Aggregator: Streamlit writes miro_plan_nudges.json,            │
│   dispatches codex_bridge.apply_plan(...). Resend send optional. │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. DELTA_REPORT  (LLM: OpenAI gpt-4o — pattern reasoning)        │
│   Reads all pre-poll + post-poll + nudge response data.          │
│   Output: Behavior change delta report → MiroDoc fragment.       │
│   Pattern: "X% of learners moved from rarely → often on          │
│   <behavior>. Top objection still surfacing: <objection from     │
│   .objections>. Recommended reinforcement: <proof_point>."       │
│   Aggregator: Streamlit writes miro_plan_delta.json,             │
│   dispatches codex_bridge.apply_plan(...).                       │
└─────────────────────────────────────────────────────────────────┘
  │
  ▼
END
```

### 4.1 Model assignment

| Node | Model (LiteLLM id) | Why |
|---|---|---|
| Phase A LLM extracts | `featherless_ai/...8B-Instruct` | High volume, low reasoning |
| Phase B per-question synthesis | `featherless_ai/...70B-Instruct` | Some reasoning, lots of calls |
| Design doc | `featherless_ai/...70B-Instruct` | Cost-conscious; quality contingent (see risks) |
| Session plan + agendas | `openai/gpt-4o` | Heaviest reasoning, structure |
| Materials (slides, polls, guide) | `openai/gpt-4o` | Quality matters most here |
| Nudges | `featherless_ai/...8B-Instruct` | High volume, light reasoning |
| Delta report | `openai/gpt-4o` | Pattern detection across data |

LLM access is unified through LiteLLM so swapping a model in any node is a one-line change in `ROLE_TO_MODEL`. Anthropic was considered for the heavy-reasoning roles but dropped — no Anthropic key available in V0; OpenAI gpt-4o is the chosen flagship.

### 4.2 Single edit point — invariant

Linda has exactly one edit checkpoint, after `design_doc` and before `session_plan`. She does not see/edit research output and does not edit materials. This keeps the demo arc clean and the implementation simple. If the design doc captures what's wrong, downstream regenerates correctly. If something downstream is wrong, the fix is in the design doc.

### 4.3 The integration session (Session 4)

Sessions 1-3 each map to one of Linda's selected behaviors (`SessionPlan.behavior_id` set). Session 4 has `behavior_id = None` and is an integration session that synthesizes across all three. Its `session_plan` prompt is given access to all three `BehaviorContext` slices and the three behavior objectives, and asked to:

- Anchor the opening on the connection between behaviors.
- Use a teach block that walks through how the three behaviors compose in a real deal motion (sourced from `findings.examples` across all three).
- Drive the practice/role-play from a multi-behavior scenario that requires switching between them.
- Capture a cross-cutting commitment in the post-poll (one commitment that touches all three).

The integration session uses the same materials sub-graph as the others; only the upstream prompt context differs.

### 4.4 Codex bridge

Python never calls the Miro REST API. Instead, every Miro write happens through a `codex exec` subprocess that drives the user's configured Miro MCP server.

**Prerequisites (one-time setup on the demo machine):**

- Codex CLI installed and on `PATH` (`codex --version` succeeds).
- Miro MCP server registered in `~/.codex/config.toml` and authorized to the user's Miro account (one-time `/login` flow inside Codex).
- `MIRO_BOARD_ID` set in `.env`.

**Invocation pattern:**

```python
# src/growme/miro/codex_bridge.py
def apply_plan(plan_path: Path, *, board_id: str, timeout: int = 300) -> CodexResult:
    if os.environ.get("USE_LIVE_MIRO", "true").lower() != "true":
        return CodexResult(status="dry_run", plan_path=str(plan_path),
                           stdout="", stderr="", exit_code=0)
    prompt = (
        f"Read the JSON plan at {plan_path}. For every item, in declared order, "
        f"call the appropriate mcp__miro__* tool against board {board_id}. "
        f"Apply each item exactly as specified — do not skip, do not reorder, do not add. "
        f"For every created item, print one line `KEY=MIRO_ID` to stdout. "
        f"When all items are applied, print `BUILD COMPLETE` and exit."
    )
    proc = subprocess.run(
        ["codex", "exec", prompt],
        capture_output=True, text=True, timeout=timeout,
    )
    status = "ok" if proc.returncode == 0 and "BUILD COMPLETE" in proc.stdout else "error"
    return CodexResult(status=status, plan_path=str(plan_path),
                       stdout=proc.stdout, stderr=proc.stderr, exit_code=proc.returncode)
```

**Streamlit UX (Wizard Step 4 + Demo Console):**

- Block on `apply_plan` with `st.spinner("Building on Miro…")`. No streaming for V0.
- On `status="ok"`: success line + 📐 Open Miro Board deep link.
- On `status="error"`: collapsible stderr panel, **Retry** button, **Show plan JSON** toggle so the user can hand the plan to Codex manually as a last resort.
- On `status="dry_run"`: "Dry-run: plan written to `<plan_path>`" + download button. Used for tests/CI.

**`USE_LIVE_MIRO=false` semantics:** the bridge writes the plan JSON to disk (the caller already wrote it before invocation; the bridge just confirms presence) and returns immediately with `status="dry_run"`. Unit tests run in this mode and assert on the JSON shape only — Codex is not a CI dependency.

**Idempotency:** Codex is told explicitly not to skip, reorder, or add items. Plan keys are deterministic (`session_1.slide_3`, `nudges.learner_03.session_1`) so a re-run after partial failure can compare what was created against the plan. (Full re-run of an already-applied plan is not supported in V0; the demo flow runs each `_*.json` once.)

### 4.5 MiroPlan intent format

The contract between Python and Codex is a JSON file matching the `MiroPlan` Pydantic schema (full fields in §9). Coordinates and parent relationships are pixel-precise — Python computes layout in `src/growme/miro/plan_builder.py`, Codex applies verbatim. Codex makes no layout decisions.

```python
# Sketch — full models in §9
class MiroPlan(BaseModel):
    frames:    list[MiroFrame]    = []
    slides:    list[MiroSlide]    = []   # texts inside frames
    polls:     list[MiroPoll]     = []   # rendered as text widgets in V0
    documents: list[MiroDoc]      = []   # facilitator guides + delta report
    cards:     list[MiroCard]     = []   # nudges
    stickies:  list[MiroSticky]   = []   # poll-response renders
```

Each item carries:
- `key: str` — deterministic identifier (e.g., `session_1.slide_3`) used by Codex to print `key=miro_id` lines on stdout.
- `parent_key: str | None` — references a `MiroFrame.key` if the item is a child.
- `x: float`, `y: float` — explicit coordinates relative to the parent (or board origin if top-level).
- `width: int`, `height: int` (where applicable).

The full plan is serialized to `.growme_sessions/<uuid>/miro_plan_{materials,nudges,delta}.json` — one file per build step. Streamlit reads back the `key=miro_id` mapping from Codex stdout to populate `SessionMaterials.miro_frame_id`, `Nudge.miro_card_id`, and `DeltaReport.miro_doc_id`.

---

## 5. Wizard flow

| Step | Page | Inputs / Outputs |
|---|---|---|
| 1 | **Company + Audience** | `company_url` (e.g., neon.tech), `company_alias` (Photon DB, prefilled), `audience_description` (textarea, placeholder: "12 mid-market AEs, 1-3 yrs tenure, expanding into healthcare") |
| 2 | **Behavior selection** | 6 checkboxes; PIC trio pre-checked. Caption shows framework_origin per item. Validates exactly 3 selected. |
| 3 | **Generation + Design doc edit** | Click "Generate" → live progress (research → design doc) → render markdown design doc in `st.text_area` (editable) → [BUILD ON MIRO] button |
| 4 | **Build progress + results** | Live progress (sessions → materials → polls → guides) → success page with deep links: "📐 Open Miro Board", "▶ Demo Console" |
| — | **Demo Console** (separate page) | Fast-forward buttons: "Simulate Session 1 complete" → seeds learner responses → triggers nudges generation → "Simulate Session 2..." → ... → "Generate Delta Report" |

Streamlit reruns the whole script on every interaction. We persist `WizardInputs`, `EnrichedContext`, `DesignDoc`, `SessionPlans`, `Materials` to pickle files keyed by a session UUID. On every page load, we hydrate state from the pickle.

---

## 6. Miro artifacts (board layout)

```
+ Top-left ─────────── Header frame: program title + cohort summary
+ Top row ──────────── Frame "Session 1: Quantify Pain"
                        ├─ Slide frames (5-8 per session, one per slide)
                        ├─ Pre-poll widget + pre-poll baseline table
                        ├─ Post-commitment poll widget + responses table
                        └─ Facilitator guide (Miro Document)
+ Top row ──────────── Frame "Session 2: Capabilities → Outcomes"  (same shape)
+ Top row ──────────── Frame "Session 3: Differentiate"             (same shape)
+ Top row ──────────── Frame "Session 4: Integration"                (same shape)
+ Mid-left ─────────── Frame "Nudges" (one card per learner per session)
+ Bottom-left ──────── Frame "Behavior Delta Report" (Miro Document)
```

Each artifact has a stable Miro item ID stored in `GrowMeState`, so we can update + re-link them throughout the run. Placement is computed in `src/growme/miro/plan_builder.py` and applied verbatim by Codex; the layout constants there are the single source of truth for board geometry.

---

## 7. The 6-Behavior Menu (locked content)

Each menu entry carries 4 pre-written research questions, one per `BehaviorFindings` bucket. The `{company}` slot fills with `WizardInputs.company_alias` at runtime. PIC trio is the demo path; the other three are deliberately distinct so the menu reads as varied.

```python
BEHAVIOR_MENU = {
    "pic_pbo_quantify_pain": BehaviorTemplate(
        id="pic_pbo_quantify_pain",
        name="Quantify customer pain in business impact terms",
        description="Reps move conversations from 'we have a problem' to "
                    "'this problem costs us $X / month / quarter.'",
        framework_origin="Command of the Message: PBO",
        research_questions=ResearchQuestions(
            examples="What public examples exist of {company}'s customers describing "
                     "pain in quantified terms? Look in case studies, G2 reviews, "
                     "earnings call mentions.",
            baselines="What ROI metrics do {company}'s customers in this vertical "
                      "typically cite (e.g., $ saved, hours saved, % efficiency gain)?",
            objections="What objections do reps face when trying to push prospects "
                       "to quantify pain? E.g., 'we don't measure that yet'.",
            proof_points="What ROI calculators, case studies with before/after metrics, "
                         "or customer testimonials with hard numbers exist for {company}?",
        ),
    ),
    "pic_rc_capabilities_outcomes": BehaviorTemplate(
        id="pic_rc_capabilities_outcomes",
        name="Connect product capabilities to required outcomes, not features",
        description="Reps stop pitching features and start tying each capability "
                    "to a specific outcome the prospect needs.",
        framework_origin="Command of the Message: RC",
        research_questions=ResearchQuestions(
            examples="What public examples show {company}'s capabilities mapped to "
                     "concrete customer outcomes (vs. generic feature lists)?",
            baselines="What outcomes do {company}'s ICP customers say they need most? "
                      "What capability-to-outcome mappings already work?",
            objections="What objections arise when reps lead with features instead of "
                       "outcomes? ('How does that help us specifically?')",
            proof_points="What customer success stories tie {company} capabilities "
                         "directly to measurable customer outcomes?",
        ),
    ),
    "pic_diff_differentiate": BehaviorTemplate(
        id="pic_diff_differentiate",
        name="Differentiate from named competitors with credible proof",
        description="Reps name competitors directly and back differentiation claims "
                    "with proof points instead of marketing language.",
        framework_origin="Command of the Message: Diff",
        research_questions=ResearchQuestions(
            examples="What named-competitor comparisons does {company} or its "
                     "customers make publicly? Comparison pages, customer reviews?",
            baselines="Which competitors do {company}'s prospects most often "
                      "evaluate against? G2 'compare' data is gold here.",
            objections="What objections do reps face when prospects say "
                       "'we're also looking at <competitor>'? Common pivots, "
                       "common stalls?",
            proof_points="Which third-party validations, switching case studies, "
                         "or head-to-head benchmarks exist for {company} vs. competitors?",
        ),
    ),
    "meddpicc_eb_engage_buyer": BehaviorTemplate(
        id="meddpicc_eb_engage_buyer",
        name="Engage the economic buyer early, not just the technical champion",
        description="Reps identify and earn time with the person who controls "
                    "budget — not just the technical evaluator.",
        framework_origin="MEDDPICC: EB",
        research_questions=ResearchQuestions(
            examples="What examples exist of {company} deals where engaging the "
                     "economic buyer early changed the outcome?",
            baselines="In {company}'s typical deal, who is the economic buyer "
                      "(title, function)? How early do reps usually meet them?",
            objections="What objections come up when champions push back on "
                       "executive intros? E.g., 'they're too busy'.",
            proof_points="What collateral exists tailored for the economic buyer "
                         "(business case templates, exec briefing decks)?",
        ),
    ),
    "meddpicc_dc_decision_criteria": BehaviorTemplate(
        id="meddpicc_dc_decision_criteria",
        name="Co-create decision criteria with the buyer",
        description="Reps shift from responding to RFP-style criteria to "
                    "shaping criteria collaboratively, biasing toward {company}'s strengths.",
        framework_origin="MEDDPICC: DC",
        research_questions=ResearchQuestions(
            examples="What public examples show {company} reps influencing "
                     "decision criteria (vs. responding to a fixed RFP)?",
            baselines="What criteria do {company}'s ICP buyers typically evaluate? "
                      "Which criteria favor {company} over competitors?",
            objections="What objections arise when reps try to add or reframe "
                       "criteria mid-cycle? ('That's not in our checklist')",
            proof_points="What buyer-collaboration tools (criteria worksheets, "
                         "evaluation frameworks) does {company} provide?",
        ),
    ),
    "universal_price_as_roi": BehaviorTemplate(
        id="universal_price_as_roi",
        name="Reframe pricing objections as ROI conversations",
        description="Reps respond to 'too expensive' by re-anchoring to ROI "
                    "and total cost of ownership, not list price.",
        framework_origin="Universal / negotiation",
        research_questions=ResearchQuestions(
            examples="What pricing objection examples surface in {company}'s "
                     "G2 reviews or case studies? How do successful customers "
                     "describe the value relative to cost?",
            baselines="What is {company}'s typical TCO/ROI story? Payback period, "
                      "cost-of-status-quo data?",
            objections="What pricing objections do reps hear most? "
                       "('Cheaper alternative', 'too expensive for us', etc.)",
            proof_points="What ROI calculators, payback case studies, or TCO "
                         "comparisons does {company} have?",
        ),
    ),
}
```

---

## 8. Demo script (8-10 min walkthrough)

| Min | Beat | What's on screen | Behind the scenes |
|---|---|---|---|
| 0:00 | "Meet Linda" — frame the problem | Streamlit landing | — |
| 0:30 | Wizard Step 1: Company + Audience | Linda enters `neon.tech` (auto-aliases to "Photon DB"), pastes audience description | — |
| 1:00 | Wizard Step 2: Behavior menu | Show all 6, PIC trio pre-checked. Linda hovers — tooltips show framework_origin. Click Next. | — |
| 1:20 | Wizard Step 3: Generation kicks off | Progress: "Researching Photon DB..." → spinning items: company snapshot ✓, customer voice ✓, vertical vocab ✓, competitors ✓ → "Researching behavior 1..." × 3 in parallel → "Generating design doc..." | LangGraph Phase A then Phase B in parallel for 3 behaviors, then design_doc node |
| 2:30 | Design doc renders, Linda edits | Markdown design doc in editable text area. Linda makes one tiny edit (e.g., changes "12 AEs" → "10 AEs"). Reads aloud the behavior objectives. | — |
| 3:30 | Click [BUILD ON MIRO] | Wizard Step 4. Progress: session 1 building... session 2... session 3... session 4... nudges queued... | session_plan + materials sub-graphs running in parallel for 4 sessions |
| 5:00 | "Let me show you what got built" | Switch to Miro tab. Pan across 4 session frames — slides, polls, facilitator guide each. Open one slide deck briefly. Open the facilitator guide for session 1. | Read-only at this point |
| 6:30 | "Now imagine the trainings happened" | Back to Streamlit Demo Console. Click "Simulate Session 1 complete" → seeded learner responses replay into Miro polls live. Pan back to Miro to show the post-poll table populating. | Replay fixture data into Miro via REST |
| 7:00 | "And nudges go out" | Click "Generate Session 1 nudges" → switch to Miro Nudges frame, see per-learner email/Slack copy, each tied to that learner's commitment. | Featherless calls per learner |
| 7:45 | Fast-forward sessions 2-4 | Click through "Simulate Session 2", "Session 3", "Session 4 complete." Watch the polls fill in across all 4 frames. | More fixtures |
| 8:30 | "And the delta report" | Click "Generate Delta Report" → Miro doc populates: % movement per behavior, top still-surfacing objection, recommended reinforcement | OpenAI gpt-4o reasoning over poll diff; one Codex subprocess to apply the doc |
| 9:30 | Wrap | Pan out to whole Miro board — 4 sessions + nudges + delta report all visible. "From a behavior gap to a measured behavior change in 10 minutes." | — |

The demo is recorded, not live. Some live-call timing variability is acceptable in editing.

### 8.1 The "wow" moments (priority order)

1. Watching Miro fill up after [BUILD ON MIRO]
2. The named-competitor differentiation in the slide content (proves research is real, not generic)
3. Per-learner personalized nudges keyed to actual commitments
4. The behavior delta report citing specific objections still surfacing

---

## 9. Data model (Pydantic)

```python
# === INPUTS ===
class WizardInputs(BaseModel):
    company_url: str             # "neon.tech"
    company_alias: str           # "Photon DB"  (used in all output rendering)
    audience_description: str
    selected_behavior_ids: list[str]   # exactly 3, validated against BEHAVIOR_MENU keys
    program_length_sessions: int = 4   # locked to 4 for V0
    session_duration_min: int = 60     # locked to 60 for V0

# === BEHAVIOR MENU ===
class ResearchQuestions(BaseModel):
    examples: str
    baselines: str
    objections: str
    proof_points: str

class BehaviorTemplate(BaseModel):
    id: str
    name: str
    description: str
    framework_origin: str
    research_questions: ResearchQuestions

# === RESEARCH OUTPUT ===
class CitedFact(BaseModel):
    text: str
    source: str          # "g2:url", "web:url", "wizard:audience_description"
    confidence: Literal["high", "medium", "low"]

class BehaviorFindings(BaseModel):
    examples: list[CitedFact] = Field(max_items=5)
    baselines: list[CitedFact] = Field(max_items=3)
    objections: list[CitedFact] = Field(max_items=5)
    proof_points: list[CitedFact] = Field(max_items=5)

class BehaviorContext(BaseModel):
    behavior_id: str
    behavior_name: str
    behavior_description: str
    framework_origin: str
    research_questions: list[str]   # the 4 questions actually asked (post-substitution)
    findings: BehaviorFindings

class BaseCompanyResearch(BaseModel):
    company_snapshot: str            # markdown summary, ~200 words
    customer_voice: list[CitedFact]  # top use cases + friction phrases from G2
    vertical_vocab: list[str]        # 10-15 domain terms
    named_competitors: list[CitedFact]  # 2-3 with 1-line positioning each

class EnrichedContext(BaseModel):
    base: BaseCompanyResearch
    per_behavior: list[BehaviorContext]   # exactly 3
    sources_used: list[str]
    research_timestamp: str

# === DESIGN DOC ===
class DesignDoc(BaseModel):
    audience_section_md: str           # Section A
    behavior_objectives: list[str]     # Section B: 3 statements
    learning_objectives: list[str]     # Section C: 4 entries (one per session)
    full_markdown: str                 # the renderable text Linda edits in Streamlit

# === SESSIONS + MATERIALS ===
class AgendaBlock(BaseModel):
    name: str             # "Opening hook" / "Teach" / etc.
    duration_min: int
    description: str

class SessionPlan(BaseModel):
    session_number: int
    title: str
    behavior_id: str | None     # None for the integration session (#4)
    learning_objective: str
    agenda: list[AgendaBlock]

class SessionMaterials(BaseModel):
    session_number: int
    miro_frame_id: str
    slide_frame_ids: list[str]
    pre_poll_id: str
    post_poll_id: str
    facilitator_guide_doc_id: str

# === SIMULATED RUNTIME ===
class LearnerResponse(BaseModel):
    learner_id: str            # "learner_01" ... "learner_08"
    learner_name: str          # "Sam Patel" (faked)
    session_number: int
    pre_poll_answers: dict[str, str]
    post_poll_commitment: str
    nudge_replied: bool

class Nudge(BaseModel):
    learner_id: str
    session_number: int
    email_subject: str
    email_body_md: str
    slack_text: str
    proof_point_used: CitedFact      # which proof_point we keyed off
    miro_card_id: str

class BehaviorMovement(BaseModel):
    behavior_id: str
    pct_moved_from_rarely_to_often: float
    pre_distribution: dict[str, int]   # {"rarely": 6, "sometimes": 2, "often": 0}
    post_distribution: dict[str, int]

class DeltaReport(BaseModel):
    behavior_movements: list[BehaviorMovement]   # one per behavior
    top_objection_still_surfacing: CitedFact
    recommended_reinforcement_md: str
    full_markdown: str
    miro_doc_id: str

# === MIRO PLAN (Codex-bridge contract) ===

class MiroFrame(BaseModel):
    key: str                               # e.g. "session_1", "nudges", "header"
    title: str
    x: float
    y: float
    width: int = 1300
    height: int = 1100
    parent_key: None = None                # frames are top-level

class MiroSlide(BaseModel):
    key: str                               # e.g. "session_1.slide_3"
    parent_key: str                        # MiroFrame.key
    title: str
    body_md: str
    x: float
    y: float
    width: int = 600

class MiroPoll(BaseModel):
    key: str                               # e.g. "session_1.pre_poll"
    parent_key: str
    kind: Literal["pre", "post_commitment"]
    question: str
    options: list[str]
    x: float
    y: float
    width: int = 400

class MiroDoc(BaseModel):
    key: str                               # e.g. "session_1.guide", "delta.report"
    parent_key: str | None                 # delta report attaches at top level
    title: str
    content_md: str
    x: float
    y: float

class MiroCard(BaseModel):
    key: str                               # e.g. "nudges.learner_03.session_1"
    parent_key: str                        # nudges frame
    title: str
    description_md: str
    x: float
    y: float

class MiroSticky(BaseModel):
    key: str                               # e.g. "session_1.pre_poll.response_2"
    parent_key: str
    content: str
    color: str = "yellow"
    x: float
    y: float

class MiroPlan(BaseModel):
    """Pixel-precise instructions for Codex to apply via mcp__miro__* tools."""
    board_id: str
    build_step: Literal["materials", "nudges", "delta", "header"]
    frames:    list[MiroFrame]    = Field(default_factory=list)
    slides:    list[MiroSlide]    = Field(default_factory=list)
    polls:     list[MiroPoll]     = Field(default_factory=list)
    documents: list[MiroDoc]      = Field(default_factory=list)
    cards:     list[MiroCard]     = Field(default_factory=list)
    stickies:  list[MiroSticky]   = Field(default_factory=list)

class CodexResult(BaseModel):
    status: Literal["ok", "error", "dry_run"]
    plan_path: str
    stdout: str
    stderr: str
    exit_code: int = 0
    item_ids: dict[str, str] = Field(default_factory=dict)   # parsed from stdout `key=miro_id`

# === ORCHESTRATOR STATE ===
class GrowMeState(TypedDict):
    wizard_inputs: WizardInputs
    miro_board_id: str

    enriched_context: EnrichedContext | None
    design_doc: DesignDoc | None
    design_doc_edited_md: str | None       # Linda's edits override design_doc.full_markdown

    session_plans: list[SessionPlan] | None
    materials: list[SessionMaterials] | None

    learner_responses: list[LearnerResponse]
    nudges: list[Nudge]
    delta_report: DeltaReport | None
```

### 9.1 Output format on the wire

JSON-wrapped Markdown for all LLM-generated content. Markdown for the human-readable narrative; JSON wrapper carries citations downstream LLMs use to validate claims. Pydantic models reject malformed LLM output as cheap insurance.

### 9.2 Provenance / anti-hallucination

Every `CitedFact` carries a `source` field and a `confidence`. Downstream LLMs are prompted to cite when generating training content. This kills the "LLM hallucinates further on top of unsourced research" anti-pattern. `confidence: low` facts are flagged as "LLM-inferred — verify" in the design doc.

---

## 10. Code layout

```
src/growme/
  app/
    streamlit_app.py        # main entry; routes between pages
    pages/
      wizard.py             # multi-step wizard (4 steps)
      demo_console.py       # fast-forward buttons
    state.py                # pickle persistence by session UUID
  graph/
    state.py                # GrowMeState TypedDict
    build.py                # LangGraph assembly
  research/
    node.py                 # entry point invoked by the graph
    base_research.py        # Phase A: 4 parallel branches
    behavior_research.py    # Phase B: 3 parallel branches
    apify_clients.py        # website-content-crawler, g2-product-scraper wrappers
    web_search.py           # Apify google-search-scraper wrapper
    citation.py             # CitedFact factory + provenance helpers
    aliasing.py             # Photon-DB-from-Neon find/replace
    fixtures/               # cached real responses, fallback data
      photon_db_base.json
      photon_db_pic_pbo.json
      photon_db_pic_rc.json
      photon_db_pic_diff.json
  design_doc/
    node.py
    prompts.py
  sessions/
    plan_node.py
    materials_node.py       # parallel sub-graph: slides + polls + facilitator
                            # emits MiroPlan fragments via plan_builder
  nudges/
    node.py
    learner_fixtures.py     # 8 fake learners + responses
  delta_report/
    node.py
  miro/
    intent.py               # MiroPlan + child models (frames, slides, polls, docs, cards, stickies)
    plan_builder.py         # pure functions building plan fragments (replaces sessions/miro_writers.py)
                            # owns layout constants: HEADER_X, SESSION_X_STEP, NUDGES_X, etc.
    codex_bridge.py         # apply_plan() — wraps subprocess.run(["codex", "exec", ...])
                            # honors USE_LIVE_MIRO; parses key=miro_id stdout
  schemas.py                # all Pydantic models in section 9
  behavior_menu.py          # the BEHAVIOR_MENU dict from section 7
  llm_clients.py            # LiteLLM client (Featherless + OpenAI)
tests/
  test_schemas.py
  test_research_smoke.py
  test_e2e_dry_run.py
docs/
  superpowers/specs/2026-05-09-growme-v0-design.md   # this file
```

---

## 11. 24-hour implementation phases

| Hour | Phase | Deliverable | Why early |
|---|---|---|---|
| 0-1 | **Skeleton** | Repo scaffold, Streamlit shell scaffolded, LangGraph hello-world, Codex CLI dry-run (emit a tiny test plan; with `USE_LIVE_MIRO=true`, invoke `codex exec` against the configured Miro MCP server and verify a frame appears), LiteLLM hello-world with Featherless + OpenAI. Required env vars (`OPENAI_API_KEY`, `FEATHERLESS_API_KEY`, `APIFY_TOKEN`, `MIRO_BOARD_ID`) and optional flags (`USE_LIVE_RESEARCH`, `USE_LIVE_MIRO`, `GROWME_SESSION_DIR`) read from `.env`. | Smoke-test all integrations *before* building anything substantial |
| 1-3 | **Wizard + state** | 4-step Streamlit wizard navigating with `st.session_state`. Step 2 renders the 6-behavior menu. Submitting persists `WizardInputs` to a pickle file. | Fully testable without any AI calls |
| 3-7 | **Research node (Phase A + B)** | Pydantic schemas, Apify clients, 4 Phase A branches in parallel, 3 Phase B branches in parallel, fixture cache in `fixtures/photon_db_*.json` | The "magic." Most algorithmically complex piece — get it right early |
| 7-10 | **Design doc node + Streamlit edit** | Featherless prompt, render markdown in `st.text_area`, [BUILD ON MIRO] button | First end-to-end milestone: Linda sees a real generated design doc |
| 10-14 | **Session plan + materials sub-graph** | LangGraph parallel branches; per-session plan-fragment emitters (`plan_builder.create_session_frame`, `write_slide`, `write_pre_poll`, `write_post_poll`, `write_facilitator_guide`); aggregate to `miro_plan_materials.json`; one `codex_bridge.apply_plan` at end of build | LangGraph nodes emit plan fragments; Codex applies them in a single subprocess per build step |
| 14-16 | **Demo Console: fast-forward + fixtures** | "Simulate Session N complete" buttons that replay seeded `LearnerResponse` data into Miro polls | Half-day buffer before the hard parts |
| 16-19 | **Nudges + Delta report** | Featherless nudge generator → MiroCard fragments → codex apply; OpenAI gpt-4o delta report writer → MiroDoc fragment → codex apply | Builds on existing data — should go quickly |
| 19-21 | **Polish: aliasing, diagrams, header frame** | Photon→Neon `replace_all`, board cosmetics, header frame with cohort summary, deep links from Streamlit | What makes the demo readable |
| 21-23 | **Demo dry runs + recording** | Run end-to-end three times, fix anything brittle. Record final take. | Buffer for actual demo prep |
| 23-24 | **Buffer / sleep** | — | Reality |

### 11.1 Definition of "demo-ready" at major milestones

- After hour 7: Apify run produces real research output for Photon DB with citations.
- After hour 10: Linda can run wizard → see design doc → edit it.
- After hour 14: [BUILD ON MIRO] populates a real Miro board with all 4 sessions.
- After hour 19: Full end-to-end demo runs.

---

## 12. Risks, mitigations, and what to mock

### 12.1 Top risks (ranked)

1. **Apify reliability / rate limits** — Mitigation: cache real responses to `fixtures/` after the first successful run; flip a `USE_LIVE_RESEARCH` flag to switch.
2. **Codex CLI subprocess reliability** — Unknown latency, can stall, may partial-apply on a transient MCP error. Mitigation: 5-minute `subprocess` timeout; on non-zero exit, surface stderr in a Streamlit expander, render a **Retry** button, and a **Show plan JSON** toggle so the user can hand the file to Codex manually as a last resort.
3. **Miro MCP server availability / auth drift** — Token expiry inside the Miro MCP would silently break a run mid-build. Mitigation: smoke the bridge at the start of each work session (`scripts/smoke_codex_bridge.py`); treat a green smoke as the gate for Phase 9-10 work.
4. **Codex prompt fidelity / idempotency** — Codex might drop items, recreate duplicates, or reorder. Mitigation: deterministic plan keys (`session_1.slide_3`, `nudges.learner_03.session_1`); the prompt explicitly forbids creativity ("apply each item exactly as specified, in order; do not skip; do not reorder; do not add"); demo flow runs each `_*.json` once per session.
5. **LangGraph state size** — `EnrichedContext` for 3 behaviors with citations can be 30-50 KB. Manageable but watch for prompt bloat in downstream nodes — pass slices, not the whole state.
6. **Featherless model quality on design doc** — Per the model assignment, `design_doc` uses Featherless. Risk: lower quality than the OpenAI flagship. Mitigation: tightly-templated prompt with strict JSON schema; if quality is poor at hour 8, swap `ROLE_TO_MODEL["design_doc"]` to `openai/gpt-4o` in one line.
7. **Multi-step wizard state on Streamlit reruns** — Streamlit reruns the whole script on every interaction. Mitigation: persist `WizardInputs`, `EnrichedContext`, `DesignDoc` to pickle files keyed by a session UUID; reload on every step.

### 12.2 What's real vs mocked

| Component | Real | Mocked |
|---|---|---|
| Apify scraping | ✅ Live by default; demo recorded, not aired live | Cached fixtures available as fallback (`USE_LIVE_RESEARCH=false`) |
| LLM calls | ✅ All real | — |
| Miro write | ✅ Live by default via `codex exec` + Miro MCP | `USE_LIVE_MIRO=false` writes plan JSON to disk and returns a dry-run result (tests/CI) |
| Learner responses | ❌ | Pre-seeded JSON for 8 fake learners |
| Email send | ❌ | Generated copy displayed in Miro card; not actually sent |
| Slack send | ❌ | Generated copy displayed in Miro card; not actually sent |
| Auth / multi-tenant | ❌ | Single hardcoded session |

### 12.3 Anti-patterns we're explicitly avoiding

1. **No source citations** → LLM hallucinates further on top of ungrounded research. Mitigation: every `CitedFact` carries a `source` field; downstream LLMs cite when generating training content.
2. **Generic competitive summary without win/loss patterns** → no actionable training. Mitigation: per-behavior `findings.objections` bucket pulls specific phrases from G2 reviews.
3. **Industry-report bloat** → vendor hype burns context window. Mitigation: structured field caps (≤5 examples, ≤3 baselines, etc.) force the LLM to triage.

---

## 13. Testing strategy (lean)

- **Schema tests**: Pydantic models reject malformed LLM outputs (cheap insurance).
- **Smoke test per node**: Each LangGraph node has a `__main__` block that runs it in isolation with fixture inputs and pretty-prints the output.
- **End-to-end dry run** at hour 21+: full live run with stopwatch, compare against expected demo timing. Target full-pipeline time: <3 min from [Generate] click to materials complete.
- **Hallucination spot-check**: manually verify 3-5 `CitedFact.source` URLs resolve and cite supporting content.
- **No unit-test farm**: not the right ROI for 24 hours.

---

## 14. Out of scope for V0 (V1+ backlog)

- Real source-document upload + ingestion
- Custom (free-text) behavior input with dynamic LLM research-question generation
- Multi-tenant / auth / persistent DB
- Real email + Slack send (Resend is a stretch goal if hour 22 is free)
- Linda edits beyond the design doc
- More than 4 sessions / non-60-minute sessions
- Programs spanning more than one company alias
- Behavior delta report comparing across multiple cohorts
- Self-serve cohort administration

---

## 15. Open items

None. All decisions made; all risks acknowledged with mitigations. Ready to plan implementation.
