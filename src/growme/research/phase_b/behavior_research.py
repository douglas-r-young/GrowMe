"""Run the 4 templated questions for one behavior, return BehaviorContext."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Literal

from pydantic import BaseModel, Field

from growme.behavior_menu import BEHAVIOR_MENU, render_questions_for_company
from growme.llm_clients import complete_json
from growme.research.citation import cited_fact, source_inference, source_web
from growme.research.web_search import WebHit, search_many
from growme.schemas import BehaviorContext, BehaviorFindings, CitedFact

Bucket = Literal["examples", "baselines", "objections", "proof_points"]


class _Finding(BaseModel):
    text: str = Field(min_length=10)
    source_url: str = ""


class _BucketResult(BaseModel):
    findings: list[_Finding] = Field(default_factory=list, max_length=5)


SYNTH_SYSTEM = (
    "You are a sales-enablement researcher synthesizing into a specific finding bucket. "
    "Given web search hits and a question, return up to 5 concrete findings. "
    "Each finding has 'text' (1-2 sentence factual statement) and 'source_url' "
    "(URL from the search hits if directly supported; empty string if inferred). "
    "Ground claims in the hits whenever possible; do not fabricate URLs."
)


def _synth_one_bucket(question: str, bucket: Bucket, hits: list[WebHit]) -> list[CitedFact]:
    blob = "\n".join(f"- [{h.title}]({h.url}): {h.content}" for h in hits) or "(no results)"
    parsed = complete_json(
        role="research_synth",
        system=SYNTH_SYSTEM,
        user=f"Question (bucket={bucket}):\n{question}\n\nWeb hits:\n{blob}",
        schema=_BucketResult,
    )
    out: list[CitedFact] = []
    for f in parsed.findings:
        if f.source_url:
            out.append(cited_fact(f.text, source_web(f.source_url), "high"))
        else:
            out.append(cited_fact(f.text, source_inference("research_synth"), "low"))
    return out


def run(behavior_id: str, company_alias: str) -> BehaviorContext:
    template = BEHAVIOR_MENU[behavior_id]
    questions = render_questions_for_company(behavior_id, company_alias)
    buckets: list[Bucket] = ["examples", "baselines", "objections", "proof_points"]

    # One Apify call covers all 4 bucket queries — collapses 4 cold-starts to 1.
    hits_by_query = search_many(questions, max_results=5)

    findings: dict[Bucket, list[CitedFact]] = {b: [] for b in buckets}

    with ThreadPoolExecutor(max_workers=4) as ex:
        future_to_bucket = {
            ex.submit(_synth_one_bucket, q, b, hits_by_query.get(q, [])): b
            for q, b in zip(questions, buckets, strict=True)
        }
        for fut in as_completed(future_to_bucket):
            bucket = future_to_bucket[fut]
            try:
                findings[bucket] = fut.result()
            except Exception as e:
                print(f"[phase_b/{behavior_id}/{bucket}] failed: {e}")
                findings[bucket] = []

    return BehaviorContext(
        behavior_id=behavior_id,
        behavior_name=template.name,
        behavior_description=template.description,
        framework_origin=template.framework_origin,
        research_questions=questions,
        findings=BehaviorFindings(
            examples=findings["examples"][:5],
            baselines=findings["baselines"][:3],
            objections=findings["objections"][:5],
            proof_points=findings["proof_points"][:5],
        ),
    )


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    ctx = run("pic_pbo_quantify_pain", "Neon")
    print(ctx.model_dump_json(indent=2)[:3000])
