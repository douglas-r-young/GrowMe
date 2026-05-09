"""LangGraph assembly. New nodes append here as they land."""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from growme.graph.state import GrowMeState
from growme.research import node as research_node


def _research(state: GrowMeState) -> GrowMeState:
    state["enriched_context"] = research_node.run(state["wizard_inputs"])
    return state


def build_research_only_graph():
    """Subgraph for the pre-edit phase: just research. Used in Wizard Step 3."""
    g = StateGraph(GrowMeState)
    g.add_node("research", _research)
    g.add_edge(START, "research")
    g.add_edge("research", END)
    return g.compile()


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    from growme.schemas import WizardInputs
    graph = build_research_only_graph()
    out = graph.invoke({
        "wizard_inputs": WizardInputs(
            company_url="neon.tech",
            company_alias="Photon DB",
            audience_description="12 mid-market AEs",
            selected_behavior_ids=[
                "pic_pbo_quantify_pain",
                "pic_rc_capabilities_outcomes",
                "pic_diff_differentiate",
            ],
        ),
        "assessment_responses": [],
        "nudges": [],
    })
    ec = out["enriched_context"]
    print(f"Got {len(ec.per_behavior)} behavior contexts; {len(ec.sources_used)} sources.")
