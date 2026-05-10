"""Generate hero / section-divider images via OpenAI gpt-image-1, with disk cache.

Cache key: SHA-256 of the (model, size, style_suffix, prompt) tuple, so changing
the brand style appendix invalidates old images.
"""
from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path

CACHE_DIR = Path(os.environ.get("GROWME_IMAGE_CACHE", Path.home() / ".cache" / "growme" / "images"))

# Editorial / abstract style appendix applied to every image. Keeps the deck
# visually coherent and prevents stocky / off-brand outputs.
STYLE_SUFFIX = (
    " — minimal modern editorial illustration, abstract geometric composition, "
    "soft gradients, plenty of white/off-white space, restrained color palette "
    "with a single blue accent (#2E5BFF), no people, no faces, no text, no logos, "
    "16:9 widescreen, suitable as a business presentation slide background."
)

MODEL = "gpt-image-1"
SIZE = "1536x1024"


def _cache_path(prompt: str) -> Path:
    key = hashlib.sha256(f"{MODEL}|{SIZE}|{STYLE_SUFFIX}|{prompt}".encode()).hexdigest()[:24]
    return CACHE_DIR / f"{key}.png"


def generate_image(prompt: str) -> Path | None:
    """Returns a local PNG path for `prompt`, or None on failure (logged, not raised).

    Slide rendering is best-effort: an image failure must not break the whole deck.
    """
    if not prompt or not prompt.strip():
        return None

    out = _cache_path(prompt)
    if out.exists() and out.stat().st_size > 0:
        return out

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        from openai import OpenAI
        client = OpenAI()
        result = client.images.generate(
            model=MODEL,
            prompt=prompt + STYLE_SUFFIX,
            size=SIZE,
            n=1,
        )
        b64 = result.data[0].b64_json
        if not b64:
            return None
        out.write_bytes(base64.b64decode(b64))
        return out
    except Exception as e:
        # Don't bring the whole deck down for a missing image.
        print(f"[images] failed to generate image: {e}")
        return None


def generate_deck_images(image_prompts: list[str]) -> list[Path | None]:
    """Sequentially generate images. Order matches input. Cache hits are instant."""
    return [generate_image(p) for p in image_prompts]
