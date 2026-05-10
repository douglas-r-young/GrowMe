"""Build the weekly nudge email (subject + HTML) for one learner.

Hackathon-tier: tries the LLM for a 1-paragraph value tied to the commitment,
falls back to a template if anything goes wrong. Always renders the Yes / No
check-in links pointing back at the local Streamlit app.
"""
from __future__ import annotations

from html import escape
from urllib.parse import quote

_SYSTEM = (
    "You are a sales coach writing one short paragraph to reinforce a learner's "
    "weekly behavior commitment. Keep it under 60 words. Be concrete and warm. "
    "Do not greet by name. Do not include sign-offs. No bullet points. Plain prose."
)


def _llm_value(commitment_text: str, week: int) -> str | None:
    try:
        from growme.llm_clients import complete

        prompt = (
            f"This is week {week} of 3.\n"
            f"The learner committed to: {commitment_text}\n\n"
            "Write a single short paragraph (under 60 words) that gives one practical, "
            "specific tip or reframe to help them follow through this week. "
            "Avoid platitudes. Avoid generic motivation."
        )
        text = complete("materials", _SYSTEM, prompt, temperature=0.5, max_tokens=240)
        cleaned = (text or "").strip()
        return cleaned or None
    except Exception:
        return None


def _fallback_value(commitment_text: str, week: int) -> str:
    return (
        f"Week {week} reminder: your commitment is — {commitment_text} "
        "Pick one real moment in your calendar this week where this is likely to come up, "
        "and write the trigger phrase on a sticky note before that meeting."
    )


def build_email(
    *,
    learner_email: str,
    learner_name: str,
    commitment_text: str,
    week: int,
    base_url: str,
    session_uuid: str,
) -> tuple[str, str]:
    value = _llm_value(commitment_text, week) or _fallback_value(commitment_text, week)

    yes_url = (
        f"{base_url}/?assessment={session_uuid}&kind=checkin"
        f"&learner={quote(learner_email)}&week={week}&done=yes"
    )
    no_url = (
        f"{base_url}/?assessment={session_uuid}&kind=checkin"
        f"&learner={quote(learner_email)}&week={week}&done=no"
    )

    subject = f"Week {week} of 3 — your GrowMe commitment"
    html = f"""\
<!doctype html>
<html><body style="font-family:-apple-system,Segoe UI,sans-serif;line-height:1.55;color:#1b2a3a;max-width:560px;margin:0 auto;padding:24px;">
  <p style="color:#c97943;font-size:12px;letter-spacing:0.12em;text-transform:uppercase;font-weight:800;margin:0 0 8px;">GrowMe · Week {week} of 3</p>
  <h2 style="font-family:Georgia,serif;font-size:22px;margin:0 0 12px;">Hi {escape(learner_name or "there")},</h2>
  <p style="margin:0 0 16px;"><strong>Your commitment:</strong> {escape(commitment_text)}</p>
  <p style="margin:0 0 24px;">{escape(value)}</p>
  <p style="margin:0 0 12px;font-weight:700;">Did you do it this past week?</p>
  <p style="margin:0 0 24px;">
    <a href="{yes_url}" style="display:inline-block;padding:10px 18px;background:#385a78;color:#fff;border-radius:8px;text-decoration:none;font-weight:700;margin-right:8px;">Yes, I did it</a>
    <a href="{no_url}" style="display:inline-block;padding:10px 18px;background:#eee7dc;color:#263f57;border-radius:8px;text-decoration:none;font-weight:700;">Not yet</a>
  </p>
  <p style="color:#65707d;font-size:13px;margin:24px 0 0;">One click logs your answer back to your training record. See you next week.</p>
</body></html>
"""
    return subject, html


def build_final_email(
    *,
    learner_email: str,
    learner_name: str,
    base_url: str,
    session_uuid: str,
) -> tuple[str, str]:
    final_url = (
        f"{base_url}/?assessment={session_uuid}&kind=final"
        f"&learner={quote(learner_email)}"
    )
    subject = "Final survey — close out your GrowMe program"
    html = f"""\
<!doctype html>
<html><body style="font-family:-apple-system,Segoe UI,sans-serif;line-height:1.55;color:#1b2a3a;max-width:560px;margin:0 auto;padding:24px;">
  <p style="color:#c97943;font-size:12px;letter-spacing:0.12em;text-transform:uppercase;font-weight:800;margin:0 0 8px;">GrowMe · Final check-in</p>
  <h2 style="font-family:Georgia,serif;font-size:22px;margin:0 0 12px;">Hi {escape(learner_name or "there")},</h2>
  <p style="margin:0 0 16px;">You've reached the end of the 3-week loop. The final 60-second survey closes out your record and shows the change since training day.</p>
  <p style="margin:0 0 24px;">
    <a href="{final_url}" style="display:inline-block;padding:12px 22px;background:#385a78;color:#fff;border-radius:8px;text-decoration:none;font-weight:700;">Take the final survey</a>
  </p>
  <p style="color:#65707d;font-size:13px;margin:24px 0 0;">Same 3 questions as the start of training. Use the same email so we can pair the scores.</p>
</body></html>
"""
    return subject, html
