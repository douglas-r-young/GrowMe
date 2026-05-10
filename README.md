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
./scripts/dev.sh
```

Starts the FastAPI backend on `http://localhost:8000` and the Vite frontend on
`http://localhost:5173` together. Ctrl-C stops both. The frontend proxies
`/api` to the backend.

To run them manually instead:

```bash
# Terminal 1
uvicorn growme.api.app:app --reload

# Terminal 2
npm --prefix frontend install
npm --prefix frontend run dev
```

## Test

```bash
pytest -v
npm --prefix frontend test
npm --prefix frontend run build
```

See `docs/superpowers/specs/2026-05-09-growme-v0-design.md` for the architecture spec.
