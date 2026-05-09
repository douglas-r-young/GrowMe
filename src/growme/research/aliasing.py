"""Replace real company name + URL with an alias. Demo-safe wrapper for Photon DB ↔ Neon."""
from __future__ import annotations

import re
from typing import Any


def alias_text(text: str, real: str, alias: str, real_url: str, alias_url: str) -> str:
    """Case-insensitive replace of real → alias in any string."""
    out = re.sub(re.escape(real_url), alias_url, text, flags=re.IGNORECASE)
    out = re.sub(re.escape(real), alias, out, flags=re.IGNORECASE)
    return out


def alias_obj(obj: Any, real: str, alias: str, real_url: str, alias_url: str) -> Any:
    """Recursively alias every string inside a JSON-like nested structure."""
    if isinstance(obj, str):
        return alias_text(obj, real, alias, real_url, alias_url)
    if isinstance(obj, dict):
        return {k: alias_obj(v, real, alias, real_url, alias_url) for k, v in obj.items()}
    if isinstance(obj, list):
        return [alias_obj(v, real, alias, real_url, alias_url) for v in obj]
    return obj
