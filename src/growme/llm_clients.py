"""LiteLLM-backed unified completion. Roles map to provider/model strings.

LiteLLM accepts model strings like:
  openai/gpt-4o
  featherless_ai/<model_name>

Anthropic was considered for heavy reasoning but dropped in V0 — no key
available; OpenAI gpt-4o is the chosen flagship.
"""
from __future__ import annotations

import json
import os

import litellm
from pydantic import BaseModel

# Role -> model id (LiteLLM format: provider/model)
ROLE_TO_MODEL: dict[str, str] = {
    "research_extract": "featherless_ai/meta-llama/Meta-Llama-3.1-8B-Instruct",
    "research_synth":   "featherless_ai/meta-llama/Meta-Llama-3.1-70B-Instruct",
    "design_doc":       "featherless_ai/meta-llama/Meta-Llama-3.1-70B-Instruct",
    "session_plan":     "openai/gpt-4o",
    "materials":        "openai/gpt-4o",
    "nudges":           "featherless_ai/meta-llama/Meta-Llama-3.1-8B-Instruct",
    "delta_report":     "openai/gpt-4o",
}


def resolve_model_for_role(role: str) -> str:
    return ROLE_TO_MODEL[role]


def complete(
    role: str,
    system: str,
    user: str,
    *,
    temperature: float = 0.3,
    max_tokens: int = 4096,
) -> str:
    """Single-shot completion. Returns the raw text content."""
    model = resolve_model_for_role(role)
    resp = litellm.completion(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=_api_key_for(model),
    )
    return resp.choices[0].message.content or ""


def complete_json(
    role: str,
    system: str,
    user: str,
    schema: type[BaseModel],
    *,
    temperature: float = 0.1,
    max_tokens: int = 4096,
    max_retries: int = 2,
) -> BaseModel:
    """Completion that must return JSON validating against `schema`. Retries with feedback."""
    schema_hint = json.dumps(schema.model_json_schema(), indent=2)
    full_system = (
        f"{system}\n\nReturn ONLY a JSON object matching this schema. "
        f"No prose, no markdown fences.\n\n{schema_hint}"
    )

    last_err: str | None = None
    for attempt in range(max_retries + 1):
        prompt = user if last_err is None else (
            f"{user}\n\nPrior attempt failed validation: {last_err}. "
            "Return strictly valid JSON for the schema above."
        )
        text = complete(
            role, full_system, prompt,
            temperature=temperature, max_tokens=max_tokens,
        )
        try:
            return schema.model_validate_json(_strip_fences(text))
        except Exception as e:
            last_err = str(e)
    raise ValueError(f"complete_json failed after {max_retries+1} attempts: {last_err}")


def _strip_fences(text: str) -> str:
    """Remove ```json ... ``` wrappers if a model adds them anyway."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else t[3:]
        if t.endswith("```"):
            t = t[:-3]
    return t.strip()


def _api_key_for(model: str) -> str | None:
    if model.startswith("openai/"):
        return os.environ["OPENAI_API_KEY"]
    if model.startswith("featherless_ai/"):
        return os.environ["FEATHERLESS_API_KEY"]
    return None
