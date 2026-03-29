#!/bin/bash
# VetClaim AI — Desktop launcher
# Double-click this file to start all servers and open the app in your browser.

ROOT="/Users/ismai/hackathon/vetclaim"
VENV_DIR="$ROOT/venv"

# ── Resolve Python (prefer venv, fall back to system) ───────
if [ -f "$VENV_DIR/bin/python3" ]; then
  PYTHON="$VENV_DIR/bin/python3"
elif command -v python3.13 &>/dev/null; then
  PYTHON="python3.13"
elif command -v python3 &>/dev/null; then
  PYTHON="python3"
else
  osascript -e 'display alert "VetClaim AI" message "Python 3 not found. Please install Python 3.13+."'
  exit 1
fi

# ── Bootstrap venv if missing ────────────────────────────────
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment and installing dependencies..."
  $PYTHON -m venv "$VENV_DIR"
  "$VENV_DIR/bin/pip" install --quiet -r "$ROOT/requirements.txt"
  PYTHON="$VENV_DIR/bin/python3"
fi

# ── Cleanup on exit ──────────────────────────────────────────
cleanup() {
  echo ""
  echo "Stopping all VetClaim AI services..."
  jobs -p | xargs kill 2>/dev/null
  wait 2>/dev/null
  echo "All services stopped."
  exit 0
}
trap cleanup INT TERM EXIT

# ── Kill anything already on these ports ────────────────────
for port in 5001 5050 5173; do
  pids=$(lsof -t -i:$port 2>/dev/null)
  [ -n "$pids" ] && echo "Clearing port $port..." && echo "$pids" | xargs kill -9 2>/dev/null && sleep 0.5
done

echo "Starting Backend API    → http://localhost:5001"
(cd "$ROOT/backend" && $PYTHON server.py 2>&1 | sed 's/^/[backend]   /') &

echo "Starting Mock VA Portal → http://localhost:5050"
(cd "$ROOT/mock_va_portal" && $PYTHON server.py 2>&1 | sed 's/^/[va-portal] /') &

echo "Starting Frontend       → http://localhost:5173"
(cd "$ROOT/frontend" && npm run dev 2>&1 | sed 's/^/[frontend]  /') &

# ── Wait for servers to be ready, then open browser ─────────
echo "Waiting for servers to start..."
for url in "http://localhost:5001/api/status" "http://localhost:5050" "http://localhost:5173"; do
  for i in $(seq 1 30); do
    curl -s -o /dev/null "$url" && break
    sleep 1
  done
done

echo "Opening browser..."
open "http://localhost:5173"
open "http://localhost:5050"

echo ""
echo "VetClaim AI is running. Close this window to stop all services."
wait
