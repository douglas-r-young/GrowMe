# GrowMe

Behavior-change training programs from a single intake.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env  # then fill in
```

## Run

```bash
streamlit run src/growme/app/streamlit_app.py
```

## Test

```bash
pytest -v
```

See `docs/superpowers/specs/2026-05-09-growme-v0-design.md` for the architecture spec.
