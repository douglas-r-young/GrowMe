#!/usr/bin/env bash
# Run the GrowMe API and Vite frontend together. Ctrl-C kills both.

set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -d frontend/node_modules ]]; then
  echo "Installing frontend dependencies..."
  npm --prefix frontend install
fi

cleanup() {
  trap - SIGINT SIGTERM
  if [[ -n "${API_PID:-}" ]] && kill -0 "$API_PID" 2>/dev/null; then
    kill "$API_PID" 2>/dev/null || true
  fi
  if [[ -n "${UI_PID:-}" ]] && kill -0 "$UI_PID" 2>/dev/null; then
    kill "$UI_PID" 2>/dev/null || true
  fi
  wait 2>/dev/null || true
}
trap cleanup SIGINT SIGTERM EXIT

PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"
if [[ ! -x "$PYTHON_BIN" ]]; then
  PYTHON_BIN="python"
fi

"$PYTHON_BIN" -m uvicorn growme.api.app:app --reload --port 8000 &
API_PID=$!

npm --prefix frontend run dev &
UI_PID=$!

echo ""
echo "GrowMe is starting:"
echo "  API:      http://localhost:8000"
echo "  Frontend: http://localhost:5173"
echo "  Ctrl-C to stop both."
echo ""

wait -n "$API_PID" "$UI_PID"
