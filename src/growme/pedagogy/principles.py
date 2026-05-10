"""Role-curated pedagogy principle bundles, extracted from `full_context.md`.

Each constant is a string designed to be f-string-concatenated into an existing
`*_SYSTEM` LLM prompt. Bundles fall into two groups:

- **Shared bundles** — small, self-contained principles reused across multiple
  prompts (anti-slop tail, behavior altitude, implementation intentions,
  stages of change, transfer, pacing, human handoff).
- **Role bundles** — composed of shared bundles + role-specific text. There is
  one role bundle per generation prompt: design_doc, session_plan, deck planner,
  facilitator guide, assessment, nudges, manager briefing.

When editing: prefer editing `full_context.md` first (the source of truth), then
update the relevant bundle here. Bundles must remain ≤2000 chars each so they
don't dominate the system prompts they're embedded in.
"""
from __future__ import annotations


# ============================================================================
# SHARED BUNDLES — reused across multiple role bundles
# ============================================================================

ANTI_SLOP_TAIL = """\
ANTI-SLOP DISCIPLINE (apply to every artifact you write):
- Pass the swap test. If you can substitute "MEDDIC" for "Challenger" and "AEs" for
  "CSMs" and the content still parses cleanly, it's slop. Rewrite until the swap
  produces something obviously wrong or specific in a different way.
- Anchor in at least 3 specifics drawn from the research context — a real customer
  phrase, a real competitor name, a real domain term, a named product. Generic
  output is a regeneration request.
- Never invent fictional company case studies. Use the real company alias from
  the research, or write `[Real customer name — facilitator inserts]` and move on.
"""
"""Source: full_context.md §2 (slop and failure modes), §10 (anti-slop checklist)."""


BEHAVIOR_ALTITUDE_PRINCIPLES = """\
BEHAVIOR ALTITUDE (the difference between a goal and a behavior):
- "Drive MEDDIC adoption" is a goal, not a behavior. A behavior is observable next
  Tuesday: "during pipeline review, the rep states the economic buyer's name and
  the budget question they last asked." If the input is goal-shaped, push it down
  to behavior altitude before generating; if you can't, name the gap explicitly.
- Apply the Mager/Pipe diagnostic: "could they do it if their life depended on it?"
  If yes, it's an environmental problem (incentives, tools, time, leadership signal),
  not a training problem. Surface that explicitly — sometimes the most useful
  output is "this isn't a training problem alone; here's what is."
"""
"""Source: full_context.md §2 F1 (wrong altitude), §3 Mager/Pipe."""


IMPLEMENTATION_INTENTION_RULES = """\
IMPLEMENTATION INTENTIONS (Gollwitzer — the actual mechanism behind commitment):
- Every commitment uses "When [specific trigger], I will [specific action]" form.
- Triggers must be event-bound or time-bound and reference something already in the
  rep's routine: a meeting type ("during pipeline review"), a tool action ("when I
  open a new opp"), a calendar event ("before Tuesday's demo"). Forbidden vague
  triggers: "when I have time", "whenever I", "during the week".
- Actions must be verifiable. "Ask the EB the budget question" beats "qualify better".
- One trigger → one action. Compound commitments fail; split or pick one.
- Where possible, stack the new behavior on an existing one ("After my pipeline
  review, I will…"). Existing routine = built-in cue.
"""
"""Source: full_context.md §3 implementation intentions, habit research."""


STAGE_OF_CHANGE_PRINCIPLES = """\
STAGE-OF-CHANGE DIVERSITY (Prochaska — different readiness in the same room):
- Skeptics (precontemplation): don't see the problem yet. Speak to them with
  credible peer voice and a concrete cost of inaction. Don't shame skepticism;
  surface a peer who used to feel the same way.
- Beginners (contemplation/preparation): see the problem, want a starting point.
  Speak to them with the smallest version of the behavior and a clear next step.
- Practitioners (action/maintenance): already doing it. Speak to them about
  relapse patterns ("around week 3 this feels harder than week 1"), refinement,
  and what to watch for.
- Differentiate tone, not content. Same behavior, three voices.
"""
"""Source: full_context.md §3 Stages of Change."""


TRANSFER_PRINCIPLES = """\
TRANSFER OF TRAINING (Baldwin & Ford — what makes the behavior stick):
- The session is the launch, not the program. Real transfer happens over weeks 2-6
  when the new behavior competes with old habits and incentives.
- Spread reinforcement across 6-8 weeks, weighted toward weeks 2-6 (the dropoff
  zone). Don't front-load week 1; don't end at week 4.
- Manager involvement is the single largest predictor of transfer. Generate
  manager-facing artifacts alongside participant-facing ones — at minimum, weekly
  "what to ask in your 1:1" prompts.
- Include relapse prevention: name the obstacles before they show up. "Around
  week 3 this will feel harder. That's the dip — Wendy Wood's research, not a
  personal failure." Pre-empted relapses are routed-around relapses.
- Measure behavior delta, not Likert confidence. "Did you ask the EB the budget
  question?" beats "How confident do you feel about budget questions?"
"""
"""Source: full_context.md §7 Transfer of Training."""


PACING_PRINCIPLES = """\
PACING & BLOCK FLOORS (Rowe wait-time research; Mind Tools cognitive load):
- Two-thirds rule: design for 65-70% explicit time fill on a 60-min session.
  Reserve 18-22 min as labeled buffer. AI-generated agendas tend to fill 95%
  and the human moments suffocate.
- Block floors (do not shrink — drop the block instead):
  - Framework / direct teach: ≤12 min uninterrupted (split larger blocks).
  - Pair discussion: ≥6 min.
  - Small-group discussion: ≥10 min.
  - Role-play / scenario practice: ≥12 min including 2 reps + debrief.
  - SME story: 90-second answerable + 2-3 min reactions = 3-4 min total.
  - Commitment drafting: ≥5 min.
  - Silent reflection: ≥30 seconds, intentional and labeled.
- Bucket ratios across the agenda: framework 20-30%, storytelling/SME 20-25%,
  activities 25-35%, discussion 20-25%, buffer 5-10%.
- No more than 6-7 distinct activity blocks per hour. Beyond that, fragmentation
  kills retention.
- Wait time: facilitator waits 4-5 seconds after every question before taking
  the first answer. Tightly choreographed agendas give zero wait time and
  the discussion never starts.
"""
"""Source: full_context.md §5-6 time distribution + pacing."""


HUMAN_HANDOFF_PRINCIPLES = """\
HUMAN HANDOFF (where AI must not pretend to fill the gap):
- AI cannot generate stories that aren't slop. Real stories require real people
  who lived the situation. AI's job: generate the **stem** — a 60-90 second
  answerable prompt with situational specificity and explicit tension. Mark
  every story slot with `[SME story slot]` so the program owner sees what they
  need to source.
  - Good stem: "Tell us about a deal you almost lost because you skipped
    qualification. What did you do when you realized?"
  - Bad stem: "Share an experience with MEDDIC."
  - Bad stem: "Tell us a success story." (No tension, no useful learning.)
- Calibration question before each framework: "How do the strongest reps here
  handle X?" Use the room's actual answers to anchor or correct the framework
  before introducing it.
- Anti-pattern callouts invite SME validation: "Common trap: leading with feature
  lists when the buyer asked about outcomes. Senior reps — does that match what
  you see?"
- Worked examples with blanks: leave the consequential parts to the SME. "Here's
  a 1:1 prep checklist a manager might use. What's the one item you'd add that
  you've learned the hard way?"
- Do NOT generate fictional case studies as a substitute for real SME stories.
  Worse than no story.
- Speaker notes / facilitator instructions on every story slot must give a
  3-step fallback: best case (senior in the room), middle (any peer), and
  failure (facilitator reads the stem and runs as paired discussion).
"""
"""Source: full_context.md §8 Where AI must hand off to humans."""


# ============================================================================
# ROLE BUNDLES — assembled from shared bundles + role-specific text
# ============================================================================

DESIGN_DOC_PRINCIPLES = f"""\
PROGRAM-DESIGN PRINCIPLES (apply to every section of the design doc you write):

{BEHAVIOR_ALTITUDE_PRINCIPLES}
{TRANSFER_PRINCIPLES}
{ANTI_SLOP_TAIL}
ROLE-SPECIFIC RULES:
1. Audience section (~200 words) must reference ≥3 specifics from the research:
   a real customer phrase from `customer_voice`, a real competitor from
   `named_competitors`, or a real domain term from `vertical_vocab`. Name the
   resistance pattern explicitly (skill / habit / incentive / fear / environment) —
   pick one or two, do not list all five. If research suggests the answer is
   environmental, surface that as a Mager/Pipe flag.
2. Each behavior_objective must be observable next Tuesday by a manager who
   wasn't in the room. "Success = learners can [observable behavior in specific
   situation]" — not "learners understand X".
3. Single integration_learning_objective synthesizes across all 3 behaviors:
   "After this 60-minute session the learner will be able to [verb] when [trigger
   condition]." V0 ships ONE 60-minute integration session — do not produce
   per-session learning objectives.
4. Transfer plan is a REQUIRED full_markdown section under heading "## Transfer
   plan". It covers: trigger event(s) the behavior fires on, the 6-8 week nudge
   cadence weighted toward weeks 2-6, the manager's role (1:1 prompt focus), the
   most likely failure modes for this audience, and what evidence proves the
   behavior changed. Do NOT bury this as a sub-section. This is the single
   largest predictor of whether the program works.
5. Mark `[SME story slot]` and `[Program owner customizes]` directly in the
   markdown wherever the program needs human input. The reader sees what AI did
   versus what they have to source.
"""


SESSION_PLAN_PRINCIPLES = f"""\
SESSION-PLANNING PRINCIPLES (binding when you build the agenda):

{PACING_PRINCIPLES}
{HUMAN_HANDOFF_PRINCIPLES}
ROLE-SPECIFIC RULES:
1. The session is ONE ~60-minute integration session covering all three behaviors.
   Total agenda minutes ∈ [55, 65].
2. Tag each AgendaBlock with a bucket field: "framework", "story", "activity",
   "discussion", or "buffer". Across the agenda the bucket ratios should land
   close to: framework 20-30%, story 20-25%, activity 25-35%, discussion 20-25%,
   buffer 5-10%. The renderer will validate these ratios; off-target plans
   regenerate.
3. Include at least one block with bucket="buffer" and duration_min ≥ 5.
   Label its description "Buffer + breathing room — questions, transitions, the
   thing someone really needs to ask. Do not fill this with content."
4. End on a commitment block (bucket="activity"), not a "key takeaways" block.
   The commitment is the bridge to the nudge schedule; takeaways are slop.
5. Ground the role-play / scenario block (≥12 min) in a multi-behavior scenario
   sourced from per-behavior findings — setup uses .examples, tension uses
   .objections, recovery uses .proof_points.
6. Where the agenda calls for a story, write the prompt that lets an SME or peer
   answer in 60-90 seconds with tension. Tag the description with [SME story slot].
"""


# Pedagogy NON-NEGOTIABLES that EXTEND the structural rules in PLANNER_SYSTEM.
# Use as a labeled section appended after the existing numbered list — the
# items are intentionally lettered (a-h) so renumbering of the host prompt's
# list doesn't drift this bundle.
DECK_PEDAGOGY_NON_NEGOTIABLES = f"""\
PEDAGOGY NON-NEGOTIABLES (extend the structural rules above with these):

a. Story stems, not stories. Where the slot calls for a peer/SME story, do NOT
   generate the story itself. Generate the *stem* — a 60-90 second answerable
   prompt with situational specificity and explicit tension. Mark the eyebrow as
   "SME story · [program owner sources]". In speaker notes write a 3-step
   fallback: best case (senior in the room), middle (any peer), failure
   (facilitator reads the stem and runs as paired discussion).
b. Calibration question before each behavior block. The first slide of each
   behavior section (the section_divider's promise OR the first teach) should
   ask the room "How do the strongest reps here handle X?" — reserve speaker-notes
   time for 2-3 answers before introducing the framework. The teach slide that
   follows says "Building on what we just heard…" rather than "[Framework] stands
   for…".
c. Anti-pattern callout in at least one example slide per behavior. Frame the
   BEFORE state as the trap most reps fall into ("Common trap: leading with
   feature lists when the buyer asked about outcomes"), not as a strawman.
d. No fictional company case studies. Every BEFORE/AFTER references the company
   alias from the research or `[Real customer name — facilitator inserts]`.
   Never invent "Acme Corp" or generic SaaS scenarios.
e. Stage-of-change diversity across the deck. At least one slide speaks to the
   skeptic ("Why this matters when X happens, even if you've already tried it").
   At least one speaks to the beginner ("Smallest version: just the first
   question"). The close slide speaks to the practitioner ("Watch for this
   relapse pattern around week 3").
f. Implementation intention on the close slide. The `commitment_recap` block
   must take "When [trigger], I will [action]" form with the trigger drawn from
   the audience's actual workflow. Triggers must be event-bound or time-bound;
   "when I have time" is forbidden.
g. Relapse-prevention beat in the integration role-play (the second activity).
   The last sub_prompt should be "Where will this be hardest? What's the moment
   in your week when you'll default to the old behavior?" This is the seed
   for week-2-and-3 nudges.
h. Speaker notes name the human handoff explicitly. Every story-slot or
   SME-validation slide's speaker notes include a sentence like "[Program owner:
   source an SME for this slot] [If no SME available: facilitator reads the
   stem and runs as paired discussion]." This is what makes the deck shippable
   without lying about what AI can and cannot do.

{ANTI_SLOP_TAIL}"""


GUIDE_FACILITATION_PRINCIPLES = f"""\
FACILITATION PRINCIPLES (apply when writing each section of the guide):

{PACING_PRINCIPLES}
ROLE-SPECIFIC RULES:
1. Wait time. After every question prompt in the guide, add the parenthetical
   "(wait 4-5 seconds — count to five before taking the first answer; if silence
   persists, name it: 'I'll give that another beat')". This is the highest-leverage
   facilitation skill and AI-generated guides routinely skip it.
2. Story slot scripts. Where the deck has an SME story slot, the guide must give
   the facilitator three options in order:
   (a) Best case — senior in the room: "Invite [Person] by name, give them the
       stem, hold space for 90 seconds + reactions";
   (b) Middle case — only juniors: "Ask 'has anyone seen this happen?' and
       accept partial answers";
   (c) Failure case — no volunteers: "Read the stem aloud, give 2 minutes for
       paired write-pair-share."
3. Objection-resistance pairing. Each objection from the research must be paired
   with: the objection verbatim, the most common reason it's surfacing (skill /
   habit / incentive / fear / environment), and the redirect that defuses it
   without dismissing the rep.
4. Buffer is on schedule. If the agenda has a buffer block, the guide must
   explicitly say "Resist the urge to fill this with more content. Let the
   silence land. The questions someone really needs to ask come out in the
   buffer." Do not let the facilitator collapse it.
5. Close with the implementation intention, not key takeaways. The "Commitment +
   close" section scripts the exact prompt the facilitator says to elicit
   "When X, I will Y" — do not summarize what was learned.
"""


ASSESSMENT_PRINCIPLES = f"""\
ASSESSMENT PRINCIPLES (the difference between measurement and measurement theater):

{IMPLEMENTATION_INTENTION_RULES}
{STAGE_OF_CHANGE_PRINCIPLES}
ROLE-SPECIFIC RULES:
1. Behavior, not confidence. Each pre-question measures whether the behavior
   occurred, not how confident the rep felt about it. BAD: "How confident are
   you about quantifying customer pain?" GOOD: "In the last week, how often did
   you ask a prospect 'how do you measure that today?' before pitching
   capabilities?" The frequency scale (Never / Rarely / Sometimes / Often /
   Always) measures observable action; do NOT slip into Likert confidence
   ("Strongly agree…").
2. Concrete, time-bound, repeatable. The question references a unit of behavior
   the rep can count. "On the calls you ran this week" beats "in your sales
   process". Where the research supplies a real customer term, use it.
3. Commitment options use "When [specific trigger], I will [specific action]"
   form. Triggers must be event-bound or time-bound — meeting type, tool action,
   or calendar event. Forbidden: "When I have time", "Whenever I remember",
   "During the week".
4. One trigger, one action per commitment. No compound commitments — split or
   pick one.
5. The 4-5 commitment_options together cover the skeptic ("smallest version:
   ask one question"), the beginner ("standard version"), and the practitioner
   ("aggressive version with a higher rep count"), so participants pick what
   matches their stage.
"""


NUDGE_PRINCIPLES = f"""\
NUDGE PRINCIPLES (every word competes with Slack and email; earn the open):

{IMPLEMENTATION_INTENTION_RULES}
{STAGE_OF_CHANGE_PRINCIPLES}
{TRANSFER_PRINCIPLES}
ROLE-SPECIFIC RULES:
1. Tied to the rep's exact commitment, not generic encouragement. Reference the
   trigger AND the action verbatim. "You committed to ask 'how do you measure
   that today?' on 3 calls this week — Tuesday's the day." FORBIDDEN: "You got
   this!", "Keep up the great work!", "Remember what you learned…".
2. Pre-empt the relapse moment. Around weeks 2-4 the new behavior feels harder
   than week 1. Name this: "If this feels harder this week than last, that's the
   dip — Wendy Wood's research, not a personal failure." Once the relapse is
   named, the rep can route around it.
3. Match the moment. The nudge fires at a time when the behavior could actually
   occur — Monday morning before the week's calls, Friday for a weekly retro,
   the night before a known demo. Slack text references the specific moment if
   the proof point gives you that hook ("before your demo this afternoon").
4. Stage-aware tone. Skeptic-aimed: "Here's why this still matters when [the
   objection they had] comes up — [proof point]." Beginner-aimed: "Smallest
   version this week: just one of the three questions." Practitioner-aimed:
   "Watch for this — the relapse pattern is X."
5. Ask for evidence, not feelings. Slack text asks "did the action happen?" —
   "Did you get the answer to the budget question? Reply Y/N." NOT "How did
   it go?" or "Feeling confident?".
6. One beat the manager can ask in their 1:1. The email body ends with: "If
   you talk to your manager this week: ask them to ask you about [specific
   behavior]." This is the lever that doubles transfer.
"""


MANAGER_BRIEFING_PRINCIPLES = f"""\
MANAGER BRIEFING PRINCIPLES (what to ask in your 1:1 over the next 6 weeks):

{TRANSFER_PRINCIPLES}
ROLE-SPECIFIC RULES:
1. The audience is the manager, not the rep. Tone is collegial, time-respecting,
   directly actionable. Length: ~600-1000 words.
2. Structure: brief framing paragraph (~80 words) explaining what the rep just
   trained on and why manager involvement matters; then sections for Week 1,
   Week 3, Week 5, Week 7 (NOT every week — the doc says weight toward weeks 2-6,
   not weight toward all weeks); then a "Watch for" section naming relapse signals.
3. Each week section has 2-3 specific 1:1 prompts grounded in the rep's
   commitment + the behaviors. Specific = the prompt names the behavior, the
   trigger, and the kind of answer to expect. BAD: "Ask about their progress."
   GOOD: "Ask: 'On the calls you ran this week, how often did you get an answer
   to the budget question before pitching capabilities? Specifically — what did
   the prospect say when you asked?'"
4. The "Watch for" section names 1-2 relapse signals per behavior. "If they say
   X, they're slipping back to the old habit. If they say Y, they're routing
   around the new behavior with a workaround." Pre-empts the slow drift.
5. Avoid HR-speak. No "leverage", "alignment", "stakeholders". Write the way a
   peer manager would email another peer manager.
6. Close with one explicit sentence on what the rep should NOT be asked:
   "Don't ask 'how confident do you feel?' — confidence isn't behavior change."
"""
