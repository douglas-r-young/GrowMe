Adult Learning & Behavior Change Context for GrowMe
Working draft v0.3 — research context and operating instructions for the GrowMe generation agent
1. Why this document exists
GrowMe collapses 40–80 hours of program design into ~15 minutes. The promise is real. The risk is that what gets generated looks like a training program but isn’t one — well-formatted slop that fails the moment a sales leader, CS lead, or L&D pro actually reads it.
This doc is the research and design context the generation agent should operate from. It does three things:
	•	Names the dominant failure modes of AI-generated training, so the agent knows what it’s working against.
	•	Compresses the relevant research — adult learning, behavior change, transfer of training — into agent-actionable form.
	•	Marks the places where the agent must hand off to humans (SMEs, managers, program owners) instead of pretending to fill in the gap itself.
Every research section ends with explicit DO/DON’T instructions for the agent.
2. What slop is, and the dominant failure modes
Defining slop
Slop is content that is structurally correct (right length, right format, right keywords) but informationally void — it could apply to any company, any audience, any behavior, with minimal edits.
The operational test: if you swap "MEDDIC" for "Challenger" and "sales reps" for "CS managers," does the content still make sense? If yes, it’s slop. The content has no actual grip on the user’s situation; it’s pattern-matched to "what training looks like" rather than "what this specific change requires."
The five dominant failure modes
Ranked roughly by how often they kill an AI-generated program. Each is paired with the GrowMe mechanism that counteracts it.
Failure 1: Wrong altitude on the behavior
the framework"Drive MEDDIC adoption" is not a behavior — it’s a goal. The AI tends to generate sessions about 
This is the single most consequential failure. When the altitude is wrong, every downstream artifact — agenda, Miro board, nudges, dashboard — is also wrong, and no amount of polish fixes it.
	•	GrowMe counter: The Define step must force the user past the goal-level statement to a specific, observable behavior. "What would a rep doing this well actually do differently next Tuesday?" If the agent can’t name a specific behavior in a specific situation, generation should not proceed.
Failure 2: Generic content with no grip on the user’s situation
theirThe AI has read 10,000 sales playbooks, leadership decks, and CS guides. It can produce something that sounds like all of them and is anchored to none. This is the failure that makes the demo feel impressive in isolation and useless when a sales leader actually reads it. They recognize the shape of training content but find nothing in it about 
	•	GrowMe counter: The Define step pulls org context (uploaded docs, URLs, playbooks) and uses real names, real situations, real artifacts throughout. If the generated session can’t reference at least 3 specifics from the user’s context, it isn’t ready to ship.
Failure 3: Confusing knowledge transfer with behavior change
Most of what AI generates is "teach them about X." Behavior change requires "get them to do X under Y conditions when Z is pulling them the other way." Different design entirely. A program built as knowledge-transfer ends with "now you understand MEDDIC." A program built for behavior change ends with "this Tuesday at 2pm, before your demo with Acme, you will run the qualification call we drafted today, and you will report back whether you got the answer to the M, E, D, D, I, and C questions before pitching."
	•	GrowMe counter: Every session ends with a real artifact — a drafted commitment with trigger, action, and a specific opportunity to perform — that becomes the seed for the nudge schedule. No "key takeaways" slides. (See Behavior Change section: Gollwitzer’s implementation intentions.)
Failure 4: No theory of resistance
Why isn’t the desired behavior happening already? AI-generated programs treat behavior change as an information gap. It almost never is. It’s usually a habit conflict ("the old way is automatic"), an incentive mismatch ("the comp plan rewards what I’m doing now"), a fear ("if I qualify hard, I’ll lose the deal"), or a missing skill ("I don’t know how to ask the economic buyer about budget without it feeling weird"). Without diagnosing which, the program prescribes the wrong intervention.
	•	GrowMe counter: The Define step explicitly probes the resistance pattern: "What’s making this behavior hard or rare today? Skill gap, habit, incentive, fear, or environment?" The generated program shape changes based on the answer. (See Behavior Change section: Mager & Pipe and Fogg’s B=MAP.)
Failure 5: Measurement theater
Pre/post Likert on "I feel confident in MEDDIC" is easy to generate, easy to ship, and tells you nothing about whether anyone qualified a deal differently. Self-reported confidence and behavior delta are not the same thing. A program that measures the former and calls it the latter has shipped a credibility problem dressed as evidence.
	•	GrowMe counter: The dashboard leads with behavior delta (was the qualification call run? was the deal qualified before the demo? did the rep ask the economic buyer the budget question?), with self-reported confidence as supporting context only. Manager observation pulses, where available, are weighted higher than self-report.
Honorable mentions (less prominent but worth tracking)
	•	Over-programming time. Every minute labeled, no buffer, human moments suffocated. Covered in detail in the Pacing section.
	•	Stopping at the session. Design ends when the workshop ends; no transfer plan. Covered in the Transfer section.
	•	Same content for everyone. Treats all participants as if they’re at the same readiness. They’re not. (See Behavior Change section: Prochaska’s Stages of Change.)
	•	Generic case studies about fictional companies. Worse than no story; signals that the program is not about you.
AGENT INSTRUCTIONS — avoiding the dominant failure modes
DO:
	•	Refuse to generate sessions when the user input is goal-level rather than behavior-level. Force a "what would they do differently next Tuesday" answer first.
	•	Anchor every session to at least 3 specifics from the user’s uploaded context (deal names, customer types, internal tool names, real situations).
	•	End every session with a behavioral commitment containing trigger + action + specific opportunity — never with a "key takeaways" slide.
	•	Probe for the resistance pattern in the Define step and let it shape session design (skill, habit, incentive, fear, environment).
	•	Lead the dashboard with behavior delta. Treat self-reported confidence as context, not headline.
DON’T:
	•	Don’t accept "drive adoption of X" as a sufficient input. That’s a goal, not a behavior.
	•	Don’t generate sessions about the framework when you should be generating sessions about the behavior the framework enables.
	•	Don’t use fictional company case studies. Use the user’s real context, or scaffold a slot for an SME to bring a real story.
	•	Don’t treat behavior change as an information gap. Most failures aren’t "they didn’t know."
	•	Don’t equate self-reported Likert shifts with behavior change in the measurement output.

3. Behavior change foundations
The L&D research community has a transfer-of-training literature (covered in section 7). But the more operationally useful research for a program designer comes from outside L&D — from behavior science, habit research, and clinical psychology. These are the frameworks that should shape what GrowMe generates.
Fogg Behavior Model: B = MAP
MotivationBJ Fogg’s model (Stanford Behavior Design Lab): a behavior occurs when 
	•	Motivation: they don’t want to do it (or want something else more strongly).
	•	Ability: they can’t do it — too hard, too time-consuming, too cognitively expensive.
	•	Prompt: nothing reminded them in the moment when the behavior could have occurred.
which leverThis is far more actionable than "transfer climate" because it tells you 
make the behavior tinyFogg’s practical implication: 
AGENT INSTRUCTIONS — using B=MAP
DO:
	•	In the Define step, diagnose which of M, A, or P is the binding constraint for this behavior. Ask the user directly if needed.
	•	For motivation problems, weight session time toward storytelling (SME stories, peer stories) and meaning-making.
	•	For ability problems, scaffold a smaller starter behavior. "Run a 2-question MEDDIC qualification" before "run a full MEDDIC qualification."
	•	For prompt problems, weight the nudge schedule heavily. Match nudges to the moments when the behavior could occur (pre-demo, end of pipeline review, before the 1:1).
	•	Tag every commitment artifact with which lever it’s pulling.
DON’T:
	•	Don’t prescribe motivational content for what is actually an ability problem. Inspirational quotes don’t help when the behavior is too hard.
	•	Don’t prescribe more training for what is actually a prompt problem. The user knows what to do; they need a reminder at the right moment.
	•	Don’t generate a starter behavior that requires high motivation AND high ability AND a perfect prompt simultaneously. Make the first rep tiny.

Implementation intentions (Gollwitzer)
"When X happens, I will do Y"Peter Gollwitzer’s research, replicated across hundreds of studies and multiple meta-analyses: a goal stated as 
This is the actual mechanism behind the commitment artifacts GrowMe should be generating. A commitment isn’t "I’ll qualify deals better." It’s "When I open a new opportunity in Salesforce, I will fill in the Economic Buyer field before the next stage."
The trigger needs to be specific, observable, and tied to something that already happens in the participant’s workflow. The action needs to be concrete enough that someone could verify whether it happened.
AGENT INSTRUCTIONS — generating commitments as implementation intentions
DO:
	•	Every commitment artifact must use "When [specific trigger], I will [specific action]" structure.
	•	Triggers must reference something already in the participant’s routine (a meeting type, a tool action, a calendar event, a recurring email).
	•	Actions must be specific enough to verify. "I will ask the economic buyer about budget" not "I will qualify better."
	•	Generate 2–3 alternate commitments per session so the participant picks one that fits their actual workflow.
	•	Capture the commitment as a structured artifact (trigger / action / first-attempt date) so the nudge engine can reference it directly.
DON’T:
	•	Don’t accept generic commitments. "I commit to using MEDDIC" is not a commitment.
	•	Don’t pair multiple actions to one trigger. One trigger → one action. Compound commitments fail.
	•	Don’t use vague triggers like "when I have time" or "during the week." If the trigger isn’t time-bound or event-bound, it never fires.

Stages of Change (Prochaska & DiClemente)
From clinical psychology (originally smoking cessation, now widely applied to organizational behavior change). People in the same room are usually in different stages of readiness:
	•	Precontemplation: doesn’t see the problem. "MEDDIC is overkill for our deals."
	•	Contemplation: sees the problem, hasn’t committed. "I should probably do this more."
	•	Preparation: committed, planning. "I want to start using this on my next deal."
	•	Action: actively doing the new behavior. "I qualified two deals with MEDDIC this week."
	•	Maintenance: sustained behavior, focus on relapse prevention. "It’s been three months and I still default to old habits under deadline pressure."
A program that treats all participants as if they’re in Action stage fails everyone in the earlier stages. The skeptic in precontemplation needs to hear from a credible peer who used to feel the same way. The contemplator needs to see what success looks like. Only the prepared and action-stage participants benefit from skill-building. Maintenance-stage participants need relapse prevention, not introduction.
AGENT INSTRUCTIONS — designing for stage diversity
DO:
	•	Generate session content that includes hooks for at least three stages (precontemplation, contemplation/preparation, action/maintenance).
	•	Use SME story slots that show the journey from skepticism to commitment, not just the highlight reel of success.
	•	Generate differentiated nudges: skeptic-aimed ("here’s why this matters when X happens"), beginner-aimed ("here’s the smallest version to try"), advanced-aimed ("here’s the relapse pattern to watch for").
	•	Include a session opener that surfaces stage diversity: "Where are you with this — skeptical, curious, ready to try, already doing it?" Lets the facilitator calibrate.
DON’T:
	•	Don’t assume everyone is in Preparation or Action. Most rooms have a healthy precontemplation contingent.
	•	Don’t generate content that shames the skeptics. They have reasons for their skepticism, often good ones.
	•	Don’t skip directly to skill-building before establishing motivation. For precontemplators, skill-building feels like an answer to a question they didn’t ask.

Performance analysis (Mager & Pipe)
Bob Mager and Peter Pipe’s "Analyzing Performance Problems" (1970, still the canonical practitioner text on this) identifies the diagnostic question that determines whether training is even the right intervention:
"Could they do it if their life depended on it?"
If yes — they could do it under sufficient pressure — training is the wrong intervention. The problem is environmental: incentives, tools, time, permission, leadership signal. Training someone harder on something they already know how to do is a category error and produces no behavior change.
If no — they genuinely can’t do it — then it’s a skill problem, and training (with practice and feedback) is appropriate.
A frighteningly large proportion of corporate training spending fails this diagnostic. Sales reps know they should qualify; the comp plan rewards them for not qualifying. CS reps know they should escalate earlier; doing so creates extra work nobody acknowledges. More training won’t fix either.
AGENT INSTRUCTIONS — applying the Mager/Pipe diagnostic
DO:
	•	In the Define step, ask explicitly: "If a participant’s job depended on this behavior tomorrow, could they do it?" If yes, surface this and recommend an environmental intervention alongside (or instead of) training.
	•	For environmental problems, generate a "manager / leadership memo" artifact alongside the program — naming the system change required for the training to land.
	•	For skill problems, weight session time toward practice and feedback (the 25–35% activity bucket) rather than framework explanation.
	•	When the answer is mixed (some skill, some environment), name both explicitly in the design doc rather than pretending it’s a pure training problem.
DON’T:
	•	Don’t silently assume training is the right intervention. Sometimes the most useful output is "this isn’t a training problem; here’s what is."
	•	Don’t generate a full program when the diagnostic comes back as environmental. Generate a smaller intervention plus the leadership-facing artifact.

Habit research (Wood, Duhigg, Clear)
Wendy Wood’s "Good Habits, Bad Habits" (2019, decades of academic research synthesized): roughly 43% of daily behaviors are habits — performed automatically in response to context cues, not chosen freshly each time. New behaviors compete with existing habits and lose unless deliberately attached to existing routines.
Practical principles, drawn from Wood’s academic work and the practitioner adaptations (Duhigg’s cue-routine-reward, Clear’s "make it obvious / easy / attractive / satisfying"):
	•	Stack the new behavior on an existing one. "After my pipeline review, I will update the MEDDIC fields on my top 3 deals." The existing behavior is the cue.
	•	Reduce friction in the moment. If the new behavior requires opening a new tool, finding a template, and remembering 6 questions, it won’t happen. Pre-stage the materials.
	•	Make the consequence visible. Behaviors stick when their effect is observable to the person doing them. Pre/post comparisons, manager acknowledgement, peer recognition all serve this.
	•	Expect the first 30–60 days to be hard. Habit formation timelines vary widely (Lally et al. 2010 found a median of 66 days, range 18–254). Programs that assume fast adoption set themselves up for "failure" at the natural slow point.
AGENT INSTRUCTIONS — designing for habit formation
DO:
	•	Generate commitments as habit stacks: "After [existing behavior], I will [new behavior]."
	•	Generate a friction audit alongside the commitment: what would the participant need to have ready to make this take <2 minutes? Pre-stage that.
	•	Build feedback visibility into the program: what will the participant see, and when, that confirms the behavior is working?
	•	Design the nudge schedule for 6–8 weeks minimum, with reinforcement densest in weeks 2–6 (the dropoff zone). Don’t front-load.
	•	Name the dip explicitly in the program. "Around week 3 this will feel harder than it did in week 1. That’s normal." Pre-empts the relapse.
DON’T:
	•	Don’t generate commitments that require building a new routine from scratch. Stack onto existing ones.
	•	Don’t assume a behavior will be habitual after 21 days. That number is folklore; real range is much wider.
	•	Don’t end the nudge schedule at week 4. The relapse risk peaks after the program "officially" ends.

4. Adult learning fundamentals
Compressed: the foundational principles that should shape session structure. The behavior-change frameworks above tell you what the program is for. These tell you how the in-session moments should feel.
Knowles’ andragogy — adults are problem-centered
Adults learn what they need to cope with situations they actually face. They bring decades of work experience that new learning must attach to or fail to stick. They engage when they understand why the learning matters to them, and they want to be treated as collaborators in their own learning, not as empty vessels.
Kolb’s experiential cycle — concrete → reflective → abstract → active
Learning consolidates through a cycle: have an experience, reflect on it, conceptualize what it means, test the concept in action. Sessions that move through all four stages outperform sessions that stop at concept introduction.
Storytelling as encoding format
Caminotti & Gray (2012) and the broader storytelling-in-L&D literature: stories activate more brain regions than facts, encode emotion alongside content, and survive longer in memory. The most valuable stories are the ones the team’s own SMEs can tell — what they tried, what didn’t work, what they wish they’d known. AI cannot manufacture these. It scaffolds the slot. (See section 8 for explicit human-handoff guidelines.)
AGENT INSTRUCTIONS — adult learning fundamentals
DO:
	•	Open every session with a problem the participant actually faces, not a framework concept.
	•	Pair every concept introduction with an experience-pull prompt ("when did you last see this in your work?").
	•	Move every session through Kolb’s four stages: experience or scenario → reflection → concept → active experimentation.
	•	Treat participants as collaborators with relevant expertise, not as students to be filled.
	•	Reserve story slots for SMEs and peers; do not generate story content directly.
DON’T:
	•	Don’t open with definitions or framework backstory.
	•	Don’t generate fictional case studies about fictional companies.
	•	Don’t skip reflection moments — the cycle breaks without them.
	•	Don’t lecture for more than 12 minutes uninterrupted (see Pacing section).

5. In-session time distribution
A note on what this is and isn’t. The 70-20-10 model (McCall, Lombardo, Eichinger / Center for Creative Leadership) describes career-long learning sources, not in-session time. Useful frame, wrong unit for this question.
The numbers below synthesize Kolb’s experiential cycle, McCarthy’s 4MAT, and decades of practitioner instructional design. Guidelines, not laws.
Mode
Share of time
What it looks like in a GrowMe session
Framework / direct instruction
20–30%
The behavior model, the criteria, the if-then loop. Tight. Not the whole hour.
Storytelling — SME and peer
20–25%
Real stories from team leaders or peers, tied to the behavior. Scaffolded slots, not generic anecdotes.
Activities / live practice
25–35%
Role-play, scenario work, drafting commitment for a real upcoming event, behavior rehearsal. Captured on Miro.
Group discussion / reflection
20–25%
Peer discussion of how the behavior shows up in their context, what blocks it, what they’ll commit to.
Buffer (intro / transitions / wrap)
5–10%
Setup, sense-making, commitment capture, close.
 
That adds to ~90–115% deliberately — real sessions overlap (a story is also discussion-bait, an activity is also reflection). The ranges describe where a moment is anchored, not exclusive buckets.
AGENT INSTRUCTIONS — time distribution
DO:
	•	Target the ranges above for any session longer than 30 minutes.
	•	For shorter sessions (15–30 min), preserve the activity and discussion shares; compress framework and buffer.
	•	Mark each agenda block with which bucket it serves so the user can sanity-check the balance.
DON’T:
	•	Don’t generate a session where framework time exceeds 30%.
	•	Don’t collapse storytelling and discussion into the same block to "save time" — they do different cognitive work.
	•	Don’t skip the buffer to fit more content.

6. Pacing and breathing room
AI-generated agendas tend to over-program time. They assume a story can land in 60 seconds, a discussion in 4 minutes, a role-play in 8 minutes. The agenda looks beautiful. In a real room, the human moments suffocate.
Wait time research (Rowe 1972; Tobin 1987)
Mary Budd Rowe’s foundational work: when a facilitator waits 3–5 seconds before taking an answer (instead of <1 second), responses get longer, more participants speak, more reasoning shows up, fewer "I don’t know"s. Tobin’s 1987 review confirmed the effect is robust across age groups, including adults.
A tightly choreographed agenda gives zero wait time. The facilitator panics at the silence in second 5 and either answers their own question or moves on. The discussion never starts.
Minimum durations for human moments
Activity
Floor
Realistic target
What AI tends to schedule
SME story (one person, one story)
90 seconds
3–4 minutes (story + 1–2 reactions)
60 seconds, no reaction time
Pair discussion (each person speaks)
6 minutes
8–10 minutes
4 minutes total
Small-group discussion (3–5 people)
10 minutes
15–20 minutes
8 minutes
Role-play / scenario practice
12 minutes
20–25 minutes (setup + 2 reps + debrief)
10 minutes
Individual reflection + writing
3 minutes
5–7 minutes
60 seconds
Commitment drafting (real artifact)
5 minutes
7–10 minutes
2 minutes
 
The two-thirds rule
Working heuristic: design for two-thirds of the available time. A 60-minute session gets ~40 minutes of substantive content and activity, with 20 minutes absorbed by transitions, late starts, the question someone really needs to ask, and the wait time above. AI-generated agendas tend to design for 95% time fill — they look more impressive and they are functionally worse.
Cognitive load and segment length
Direct-instruction segments need to break for processing. Mind Tools and broader instructional-design consensus: lecture/framework segments ≤30 minutes, ideally far less. For corporate adults already fragmented by Slack and calendar overload, the practical ceiling is 10–12 minutes before active processing has to happen.
AGENT INSTRUCTIONS — pacing
DO:
	•	Apply the two-thirds rule: target 65–70% explicit time fill, label the rest as buffer.
	•	Honor the floors in the minimum-duration table. If a slot doesn’t fit, drop it; don’t shrink it.
	•	Schedule at least one explicit silent reflection moment per session (30+ seconds, labeled).
	•	Cap any framework block at 12 minutes uninterrupted. If it needs more, cut content.
	•	Cap distinct activity blocks at 6–7 per hour. More than that = fragmentation, nothing lands.
DON’T:
	•	Don’t fill 95% of the time.
	•	Don’t schedule a story for under 90 seconds. A truncated story is worse than no story.
	•	Don’t schedule a pair discussion for under 6 minutes.
	•	Don’t skip reflection to "stay on schedule." Reflection is on schedule.
	•	Don’t generate more than 6–7 distinct activity blocks per hour.

7. Transfer of training
Behavior change is what GrowMe is for. The product overview is explicit: "from blank page to proven behavior change." Forty years of L&D research on transfer of training tells us this is hard.
The transfer problem
	•	The "10% delusion" estimate (Georgenson 1982, cited often). Methodologically loose, but captures the gap practitioners actually see.
	•	A more empirically grounded number: Canadian longitudinal study found trainees apply 54% immediately, 15% at six months, 11% at one year. Transfer falls off a cliff in the first six months without reinforcement.
	•	Only 25% of training participants in a McKinsey survey said training measurably improved their performance.
	•	Only 12% of employees (HBR-cited) apply new L&D skills to their jobs.
Baldwin & Ford (1988): the canonical model
Three categories of inputs determine whether training transfers:
	•	Trainee characteristics: motivation, self-efficacy, ability. (GrowMe touches via the Define step.)
	•	Training design: identical elements, behavioral modeling, practice with feedback. (GrowMe touches via session generation choices.)
	•	Work environment: manager support, peer support, opportunity to perform, transfer climate. This is the factor most training programs ignore and the one most predictive of transfer. (GrowMe’s nudge system + manager-facing artifacts are the lever for this.)
Highest-evidence transfer interventions
Intervention
Mechanism
GrowMe surface
Implementation intentions / goal setting
Pre-loads action to a specific cue (~2x effect on follow-through).
Commitment artifact at end of every session.
Relapse prevention
Surfaces likely setbacks during training so learners pre-plan responses.
"What could derail this?" prompt in final session, surfaced again as week 2–3 nudge.
Manager involvement
Largest single environmental predictor of transfer.
Manager-facing nudges and 1:1 prompt artifacts.
Peer cohort accountability
Social pressure and shared identity sustain motivation.
Cohort-level nudges and shared commitment visibility.
Spaced reinforcement
Combats the steep forgetting/transfer dropoff in weeks 2–6.
Nudge schedule weighted across weeks 2–6, not front-loaded.
Behavioral feedback loops
Closes see-do-reflect cycle; behavior fades without it.
Pre/post assessment + commitment-completion data.
 
Reframe for the team: GrowMe is not a session generator that also sends nudges. GrowMe is a transfer engine that uses sessions to launch the behavior change. The session agenda is the smallest part of what makes the program work.
AGENT INSTRUCTIONS — transfer planning
DO:
	•	Make "Transfer plan" a required section in every generated design doc — behavior, trigger, cadence, manager role, failure modes, evidence.
	•	Default the nudge schedule to 6–8 weeks, weighted toward weeks 2–6.
	•	Generate manager-facing artifacts alongside participant-facing ones. At minimum: weekly "what to ask in your 1:1" prompts.
	•	Include a relapse prevention moment in the final session. Capture named obstacles and pre-commitments; feed into nudge content.
	•	Allocate 10–15% of in-session time to transfer work (commitment drafting, obstacle-anticipation, scheduling first attempt).
	•	Generate behavior-focused pre/post assessment items. Where possible, manager-observation pulses outweigh self-report.
DON’T:
	•	Don’t front-load nudges in week 1. The dropoff is in weeks 2–6.
	•	Don’t skip the manager-facing layer. It’s the highest-leverage intervention.
	•	Don’t end nudges at week 4 — that’s when relapse risk peaks.
	•	Don’t lead the dashboard with completion or satisfaction scores. Lead with behavior delta.

8. Where AI must hand off to humans
There are things AI cannot reliably do, no matter how good the prompt. A useful program acknowledges these limits explicitly and designs slots where humans (SMEs, managers, program owners, participants themselves) bring the wisdom AI can’t generate.
What AI cannot do well, even with great context
	•	Diagnose why a behavior isn’t happening. Requires real conversation with people in the system. The Define step can probe; it can’t observe.
	•	Generate stories that aren’t slop. Real stories require real people who lived the situation. AI can design the slot and the prompt; the SME has to bring the story.
	•	Calibrate emotional weight. When is a topic sensitive? When is humor appropriate? When is the room exhausted? AI can’t read the room.
	•	Know what’s politically charged inside the customer’s org. The unsayable thing is unsayable for a reason; AI doesn’t know what it is.
	•	Adjust mid-session based on what’s actually happening. A live facilitator does this. AI-generated agendas are static.
	•	Validate that the behavior actually matters in this context. Sometimes the user’s stated behavior is wrong. Only a peer or domain expert can call this out.
Slot patterns that pull human wisdom into the program
For each AI limitation, there’s a content pattern that scaffolds the human contribution rather than trying to fake it.
Story stems for SMEs
Pre-written prompts an SME can answer in 60–90 seconds (with 2–3 minutes of total airtime including reactions). Specific, situational, with a clear emotional center.
	•	Good stem: "Tell us about a deal you almost lost because you skipped qualification. What did you do when you realized?"
	•	Bad stem: "Share an experience with MEDDIC."
	•	Bad stem: "Tell us a success story." (No tension, no useful learning.)
Anti-pattern callouts (for SME validation)
Frame the content around a failure mode AI thinks the audience falls into, then invite a senior SME to confirm or correct. "Common trap: managers default to fixing the work themselves under deadline pressure. Senior leaders here — does that match what you see?" Builds in a wisdom check that can shift the program in real time.
Worked examples with blanks
Generate a partially completed real-feeling example, leave the consequential parts blank, ask the SME or participant to fill them. "Here’s a 1:1 prep checklist a manager might use. What’s the one item you’d add that you’ve learned the hard way?"
Calibration questions before the framework
Before introducing a framework, ask the room (or the SME pool): "How do the strongest people here handle X?" Use the actual answers to anchor or correct the generic framework. This both surfaces local wisdom and makes the framework feel less imposed.
Barrier validation
The resistance patterns the agent generates in the Define step are AI-drafted defaults. Ship them past 2–3 SMEs first: "Are these the actual things that get in your team’s way?" The answer reshapes the commitment templates and the relapse prevention work.
"Where this is hardest" prompts
Have participants name where they expect to relapse, and what they’ll do when the relapse moment arrives. AI can generate the prompt and the structure; only the participant knows the real answer.
When to hand off, by program stage
Stage
Where AI does the work
Where humans must fill in
Define
Probe questions, structure, capturing context.
Diagnosing actual resistance pattern; validating that this is the right behavior.
Review (design doc)
Session architecture, flow, time allocation, transfer plan.
Program owner’s judgment on whether the proposed design fits the org’s reality.
Build (sessions, Miro, nudges)
Agenda, slots, prompts, structures, draft nudge content.
SMEs filling story slots; program owner customizing nudge tone for their channel.
Launch
Scheduling, sequencing, channel routing.
Manager involvement; live facilitation if synchronous; cohort-level adjustments.
Measure
Aggregating data, generating dashboard.
Interpreting whether observed behavior change is meaningful in context.
 
AGENT INSTRUCTIONS — human handoff
DO:
	•	For every story in a session, generate a story stem with a specific situational hook (90 seconds answerable, with tension). Reserve a 3–4 minute slot. Mark it as "[SME story slot]" so the program owner knows to source it.
	•	Generate 2–3 alternate story stems per slot so the SME can pick.
	•	Generate "anti-pattern callout" prompts that explicitly invite SME validation or correction.
	•	Generate "calibration question" openers before any framework introduction.
	•	Generate a "where this is hardest" prompt for the final session, capturing participant-specific obstacles.
	•	Mark every human-handoff slot clearly in the design doc and Miro board. The program owner needs to know what AI did and what they need to source.
DON’T:
	•	Don’t generate the story content itself. Generate the slot, the prompt, and the structure.
	•	Don’t use fictional case studies as a substitute for a real SME story. Worse than no story.
	•	Don’t hide the human-handoff requirements. The user should see clearly which slots need their or their SMEs’ contribution.
	•	Don’t pretend the AI can calibrate emotional or political nuance. Flag where the program owner should review for tone.

9. Per-step agent instructions
Mapping all the above onto GrowMe’s five-step flow.
Step 1 — Define
AGENT INSTRUCTIONS — Define step
DO:
	•	Force the user past goal-level statements to a specific, observable behavior ("what would they do differently next Tuesday").
	•	Probe for the resistance pattern (Mager/Pipe diagnostic + Fogg M/A/P).
	•	Pull org context (uploaded docs, URLs, playbooks) and tag specific names, situations, and artifacts to use throughout.
	•	Capture the program owner’s motivation and an inferred participant motivation.
	•	Flag environmental issues (incentives, tools, leadership signal) that may need a non-training intervention.
DON’T:
	•	Don’t accept "drive adoption of X" as a sufficient input.
	•	Don’t skip the resistance diagnostic.
	•	Don’t generate a program when the diagnostic reveals it’s an environmental problem; generate a smaller intervention plus a leadership-facing artifact.

Step 2 — Review (the design doc)
AGENT INSTRUCTIONS — Review step
DO:
	•	Make "Transfer plan" a required section.
	•	Show the in-session time-distribution targets explicitly so the user can sanity-check.
	•	Show the nudge schedule as a 6–8 week timeline, not a count.
	•	Show buffer time visibly — "20 minutes for transitions and breathing room" is a feature, not an oversight.
	•	Mark every human-handoff slot (story stems, calibration questions, SME validation moments) so the user knows what they need to source.
DON’T:
	•	Don’t bury the transfer plan in a sub-section.
	•	Don’t hide the buffer time.
	•	Don’t generate sessions that fill 95% of available time.

Step 3 — Build (agenda + Miro + nudges)
AGENT INSTRUCTIONS — Build step
DO:
	•	Generate Miro boards with explicit slots: framework block, story stem prompt, individual reflection space, pair discussion space, commitment artifact.
	•	Use implementation-intention structure ("When X, I will Y") for every commitment artifact.
	•	Generate 2–3 alternate commitments per session so participants pick what fits their workflow.
	•	Generate manager-facing nudges as a separate stream from participant-facing.
	•	Generate a "common obstacles" prompt and corresponding pre-commitment template for relapse prevention.
	•	Stack new behaviors on existing routines wherever possible ("After my pipeline review, I will...").
DON’T:
	•	Don’t generate story content directly. Generate story stems and reserve real slots.
	•	Don’t generate compound commitments (one trigger → multiple actions).
	•	Don’t use vague triggers ("when I have time"). Trigger must be event-bound or time-bound.

Step 4 — Launch (nudges)
AGENT INSTRUCTIONS — Launch step
DO:
	•	Spread nudges across 6–8 weeks, weighted toward weeks 2–6.
	•	Mix nudge types: commitment reminders, reflection prompts, peer-share prompts, manager check-ins, evidence-collection asks.
	•	Tie each nudge to a specific behavior + commitment + opportunity to perform.
	•	Differentiate by stage of change: skeptic-aimed, beginner-aimed, advanced-aimed nudges as appropriate.
	•	Match nudges to the moments when the behavior could fire (pre-demo, pipeline review, before 1:1).
DON’T:
	•	Don’t front-load nudges to week 1.
	•	Don’t generate generic encouragement ("you got this!"). Tie to specific behavior and commitment.
	•	Don’t end the schedule at week 4.

Step 5 — Measure
AGENT INSTRUCTIONS — Measure step
DO:
	•	Lead the dashboard with behavior delta (pre/post assessment shift on target behaviors).
	•	Show nudge engagement and commitment-completion as supporting evidence, not headline metrics.
	•	Surface manager-involvement signal as its own number — most predictive transfer factor.
	•	Use behavior-focused assessment items, not confidence-focused ("Did you ask the EB the budget question?" not "How confident are you about budget questions?").
	•	Where possible, weight manager-observation higher than self-report.
DON’T:
	•	Don’t lead with completion or satisfaction scores.
	•	Don’t equate Likert confidence shifts with behavior change in any headline metric.
	•	Don’t hide low manager-involvement signal — name it as the transfer risk it is.

10. Anti-slop checklist
Run a generated piece of content past these before it ships. If it fails any, regenerate or hand back.
Per-session checks
	•	☐ Names a real situation. Not "feedback is important" but a specific scenario the audience faces.
	•	☐ Anchored to user context. References at least 3 specifics from the user’s uploaded docs/URLs.
	•	☐ Has SME story slot with tight stem. 60–90 seconds answerable, with tension, ≥ 3 minutes total airtime.
	•	☐ Has live practice that produces an artifact. Real draft, commitment, or calendar block.
	•	☐ Has structured discussion with adequate time. ≥6 min pair, ≥10 min small group.
	•	☐ Commitment uses implementation-intention structure. "When X, I will Y."
	•	☐ Framework time ≤30%. No single block exceeds 12 minutes uninterrupted.
	•	☐ Two-thirds time fill. Doesn’t pack 95% of the available time.
	•	☐ Includes silent reflection. ≥30 seconds, intentional and labeled.
	•	☐ No fictional company case studies. SME stories or none.
	•	☐ Human-handoff slots marked clearly. Program owner knows what to source.
Per-program checks
	•	☐ Behavior is at the right altitude. Specific, observable, executable next Tuesday.
	•	☐ Resistance pattern is named. Skill, habit, incentive, fear, or environment — at least one identified.
	•	☐ Mager/Pipe diagnostic passed. If they could do it under threat, training is wrong intervention; flag this.
	•	☐ Stages-of-change diversity addressed. Content works for skeptics, not just for the prepared.
	•	☐ Transfer plan section exists. Behavior, trigger, cadence, manager role, failure modes, evidence.
	•	☐ Nudge schedule spans 6–8 weeks, weighted to weeks 2–6. 
	•	☐ Manager-facing artifacts present. "What to ask in your 1:1" prompts at minimum.
	•	☐ Final session includes relapse prevention. Named obstacles + pre-commitments fed into nudge content.
	•	☐ Pre/post assessment is behavior-focused. Did they do X, not did they feel confident about X.
	•	☐ Passes the swap test. Swap "MEDDIC" for "Challenger" — does the program still make sense? If yes, it’s slop.
11. Sources
Behavior change
	•	Fogg, BJ (2019). Tiny Habits. Behavior = Motivation × Ability × Prompt.
	•	Gollwitzer, P. M. (1999). Implementation intentions: Strong effects of simple plans. American Psychologist.
	•	Gollwitzer & Sheeran (2006). Implementation intentions and goal achievement: A meta-analysis. Advances in Experimental Social Psychology.
	•	Prochaska & DiClemente (1983, ongoing). Transtheoretical Model / Stages of Change.
	•	Mager, R. & Pipe, P. (1970, revised 1997). Analyzing Performance Problems.
	•	Wood, W. (2019). Good Habits, Bad Habits.
	•	Lally et al. (2010). How are habits formed? European Journal of Social Psychology. (66-day median, range 18–254.)
Adult learning
	•	Knowles, M. (1980). The Modern Practice of Adult Education.
	•	Kolb, D. (1984). Experiential Learning.
	•	McCarthy, B. (1980). 4MAT System.
	•	Caminotti & Gray (2012). The effectiveness of storytelling on adult learning. Journal of Workplace Learning.
Pacing and facilitation
	•	Rowe, M. B. (1972, 1986). Wait-time research.
	•	Tobin, K. (1987). The role of wait time in higher cognitive level learning. Review of Educational Research.
	•	Brown Sheridan Center; Harvard GSE; infed.org facilitation guide.
Transfer of training
	•	Baldwin, T. T. & Ford, J. K. (1988). Transfer of training: A review and directions for future research. Personnel Psychology.
	•	Blume, Ford, Baldwin & Huang (2010). Transfer of training: A meta-analytic review. Journal of Management.
	•	Burke & Hutchins (2007). Training transfer: An integrative literature review. Human Resource Development Review.
	•	Rahyuda, Syed & Soltani (2014). The role of relapse prevention and goal setting in training transfer enhancement.
	•	Saks & Belcourt (Canadian longitudinal). 54%/15%/11% transfer dropoff at immediate / 6 months / 1 year.
12. Open questions
	•	Hackathon scope: minimum viable SME involvement when stories can’t be sourced live. What’s the smallest scaffold that still avoids slop?
	•	Async vs. synchronous sessions: how do pacing and human-handoff guidelines translate when there’s no live facilitator?
	•	Industry-specific failure modes: sales enablement, L&D, CS playbook rollouts, ops/process change all fail differently. Worth a section once we’ve seen real examples.
	•	How aggressive should manager-involvement asks be? Too little = transfer suffers. Too much = managers disengage.
	•	Should the transfer plan be visible to participants or only to the program owner?
	•	What’s the simplest credible behavior-delta measurement? Pre/post Likert is easy and gameable; manager-observation is credible but requires buy-in. Hybrid?
