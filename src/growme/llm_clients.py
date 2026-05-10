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
import threading
from contextlib import nullcontext

import json_repair
import litellm
from pydantic import BaseModel


def _provider_limit(provider: str, default: int) -> threading.Semaphore:
    env_key = f"{provider.upper()}_MAX_CONCURRENCY"
    n = int(os.environ.get(env_key, default))
    return threading.Semaphore(max(1, n))


_PROVIDER_LIMITS: dict[str, threading.Semaphore] = {
    "featherless_ai": _provider_limit("featherless_ai", 4),
}

# Pick the fastest available llama-70B-class provider for research + design_doc.
# Cerebras > Groq > Featherless on raw inference speed; if a faster provider's
# API key is set we use it, otherwise fall back so nothing breaks.
def _fast_llama_model() -> str:
    if os.environ.get("CEREBRAS_API_KEY"):
        return "cerebras/llama-3.3-70b"
    if os.environ.get("GROQ_API_KEY"):
        return "groq/llama-3.3-70b-versatile"
    return "featherless_ai/meta-llama/Meta-Llama-3.1-70B-Instruct"


def _fast_small_model() -> str:
    if os.environ.get("CEREBRAS_API_KEY"):
        return "cerebras/llama-3.3-70b"  # cost no object; same model
    if os.environ.get("GROQ_API_KEY"):
        return "groq/llama-3.1-8b-instant"
    return "featherless_ai/meta-llama/Meta-Llama-3.1-8B-Instruct"


_FAST_LLAMA = _fast_llama_model()
_FAST_SMALL = _fast_small_model()

# Role -> model id (LiteLLM format: provider/model)
ROLE_TO_MODEL: dict[str, str] = {
    "research_extract":  _FAST_SMALL,
    "research_synth":    _FAST_LLAMA,
    "design_doc":        _FAST_LLAMA,
    "session_plan":      "openai/gpt-4o",
    "materials":         "openai/gpt-5.1",
    "deck_planner":      "openai/gpt-5.1",
    "nudges":            _FAST_SMALL,
    "delta_report":      "openai/gpt-4o",
    "manager_briefing":  _FAST_LLAMA,   # Phase β: 1:1 prompts — collegial tone, less reasoning than deck
    "deck_auditor":      _FAST_LLAMA,   # Phase γ: anti-slop check on deck plan — cheap pass
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
    provider = model.split("/", 1)[0]
    gate = _PROVIDER_LIMITS.get(provider) or nullcontext()
    with gate:
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
    max_tokens: int = 8000,
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
        stripped = _strip_fences(text)
        try:
            return schema.model_validate_json(stripped)
        except Exception as e:
            # Tier 1: tolerate raw control chars (\n, \t, \r) inside string values.
            # Llama-class models routinely emit literal newlines inside long markdown
            # fields. json.loads(..., strict=False) accepts them; pydantic's
            # model_validate (no _json suffix) takes a Python dict, bypassing
            # pydantic-core's strict JSON parser.
            try:
                data = json.loads(stripped, strict=False)
                return schema.model_validate(data)
            except Exception:
                pass
            # Tier 2: structural repair (missing commas, unbalanced braces).
            try:
                repaired = json_repair.repair_json(stripped)
                return schema.model_validate_json(repaired)
            except Exception as e2:
                last_err = f"{e} | repair: {e2}"
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
    if model.startswith("cerebras/"):
        return os.environ["CEREBRAS_API_KEY"]
    if model.startswith("groq/"):
        return os.environ["GROQ_API_KEY"]
    return None
