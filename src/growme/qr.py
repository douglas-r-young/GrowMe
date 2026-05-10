"""Generate a QR PNG for a URL. In-memory only — caller saves if needed."""
from __future__ import annotations

import io

import qrcode


def generate_qr_png(url: str) -> bytes:
    """Returns PNG bytes for `url`. Box size + border tuned for slide embedding."""
    img = qrcode.make(url, box_size=10, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
