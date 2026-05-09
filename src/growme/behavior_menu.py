"""The 6-behavior menu. Linda picks 3. PIC trio is pre-checked for the demo."""
from growme.schemas import BehaviorTemplate, ResearchQuestions

BEHAVIOR_MENU: dict[str, BehaviorTemplate] = {
    "pic_pbo_quantify_pain": BehaviorTemplate(
        id="pic_pbo_quantify_pain",
        name="Quantify customer pain in business impact terms",
        description=(
            "Reps move conversations from 'we have a problem' to "
            "'this problem costs us $X / month / quarter.'"
        ),
        framework_origin="Command of the Message: PBO",
        research_questions=ResearchQuestions(
            examples=(
                "What public examples exist of {company}'s customers describing "
                "pain in quantified terms? Look in case studies, G2 reviews, "
                "earnings call mentions."
            ),
            baselines=(
                "What ROI metrics do {company}'s customers in this vertical "
                "typically cite (e.g., $ saved, hours saved, % efficiency gain)?"
            ),
            objections=(
                "What objections do {company}'s reps face when trying to push prospects "
                "to quantify pain? E.g., 'we don't measure that yet'."
            ),
            proof_points=(
                "What ROI calculators, case studies with before/after metrics, "
                "or customer testimonials with hard numbers exist for {company}?"
            ),
        ),
    ),
    "pic_rc_capabilities_outcomes": BehaviorTemplate(
        id="pic_rc_capabilities_outcomes",
        name="Connect product capabilities to required outcomes, not features",
        description=(
            "Reps stop pitching features and start tying each capability "
            "to a specific outcome the prospect needs."
        ),
        framework_origin="Command of the Message: RC",
        research_questions=ResearchQuestions(
            examples=(
                "What public examples show {company}'s capabilities mapped to "
                "concrete customer outcomes (vs. generic feature lists)?"
            ),
            baselines=(
                "What outcomes do {company}'s ICP customers say they need most? "
                "What capability-to-outcome mappings already work?"
            ),
            objections=(
                "What objections arise when {company}'s reps lead with features instead of "
                "outcomes? ('How does that help us specifically?')"
            ),
            proof_points=(
                "What customer success stories tie {company} capabilities "
                "directly to measurable customer outcomes?"
            ),
        ),
    ),
    "pic_diff_differentiate": BehaviorTemplate(
        id="pic_diff_differentiate",
        name="Differentiate from named competitors with credible proof",
        description=(
            "Reps name competitors directly and back differentiation claims "
            "with proof points instead of marketing language."
        ),
        framework_origin="Command of the Message: Diff",
        research_questions=ResearchQuestions(
            examples=(
                "What named-competitor comparisons does {company} or its "
                "customers make publicly? Comparison pages, customer reviews?"
            ),
            baselines=(
                "Which competitors do {company}'s prospects most often "
                "evaluate against? G2 'compare' data is gold here."
            ),
            objections=(
                "What objections do {company}'s reps face when prospects say "
                "'we're also looking at <competitor>'? Common pivots, "
                "common stalls?"
            ),
            proof_points=(
                "Which third-party validations, switching case studies, "
                "or head-to-head benchmarks exist for {company} vs. competitors?"
            ),
        ),
    ),
    "meddpicc_eb_engage_buyer": BehaviorTemplate(
        id="meddpicc_eb_engage_buyer",
        name="Engage the economic buyer early, not just the technical champion",
        description=(
            "Reps identify and earn time with the person who controls "
            "budget — not just the technical evaluator."
        ),
        framework_origin="MEDDPICC: EB",
        research_questions=ResearchQuestions(
            examples=(
                "What examples exist of {company} deals where engaging the "
                "economic buyer early changed the outcome?"
            ),
            baselines=(
                "In {company}'s typical deal, who is the economic buyer "
                "(title, function)? How early do reps usually meet them?"
            ),
            objections=(
                "What objections come up when {company}'s champions push back on "
                "executive intros? E.g., 'they're too busy'."
            ),
            proof_points=(
                "What collateral does {company} have tailored for the economic buyer "
                "(business case templates, exec briefing decks)?"
            ),
        ),
    ),
    "meddpicc_dc_decision_criteria": BehaviorTemplate(
        id="meddpicc_dc_decision_criteria",
        name="Co-create decision criteria with the buyer",
        description=(
            "Reps shift from responding to RFP-style criteria to "
            "shaping criteria collaboratively, biasing toward {company}'s strengths."
        ),
        framework_origin="MEDDPICC: DC",
        research_questions=ResearchQuestions(
            examples=(
                "What public examples show {company} reps influencing "
                "decision criteria (vs. responding to a fixed RFP)?"
            ),
            baselines=(
                "What criteria do {company}'s ICP buyers typically evaluate? "
                "Which criteria favor {company} over competitors?"
            ),
            objections=(
                "What objections arise when {company}'s reps try to add or reframe "
                "criteria mid-cycle? ('That's not in our checklist')"
            ),
            proof_points=(
                "What buyer-collaboration tools (criteria worksheets, "
                "evaluation frameworks) does {company} provide?"
            ),
        ),
    ),
    "universal_price_as_roi": BehaviorTemplate(
        id="universal_price_as_roi",
        name="Reframe pricing objections as ROI conversations",
        description=(
            "Reps respond to 'too expensive' by re-anchoring to ROI "
            "and total cost of ownership, not list price."
        ),
        framework_origin="Universal / negotiation",
        research_questions=ResearchQuestions(
            examples=(
                "What pricing objection examples surface in {company}'s "
                "G2 reviews or case studies? How do successful customers "
                "describe the value relative to cost?"
            ),
            baselines=(
                "What is {company}'s typical TCO/ROI story? Payback period, "
                "cost-of-status-quo data?"
            ),
            objections=(
                "What pricing objections do {company}'s reps hear most? "
                "('Cheaper alternative', 'too expensive for us', etc.)"
            ),
            proof_points=(
                "What ROI calculators, payback case studies, or TCO "
                "comparisons does {company} have?"
            ),
        ),
    ),
}


def default_pic_behavior_ids() -> list[str]:
    """The PIC trio, pre-checked in the wizard for the demo."""
    return [
        "pic_pbo_quantify_pain",
        "pic_rc_capabilities_outcomes",
        "pic_diff_differentiate",
    ]


def render_questions_for_company(behavior_id: str, company_alias: str) -> list[str]:
    """Substitute {company} in the 4 questions; return them as a list in canonical order."""
    rq = BEHAVIOR_MENU[behavior_id].research_questions
    return [
        rq.examples.format(company=company_alias),
        rq.baselines.format(company=company_alias),
        rq.objections.format(company=company_alias),
        rq.proof_points.format(company=company_alias),
    ]
