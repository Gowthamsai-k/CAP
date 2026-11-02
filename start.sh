#!/usr/bin/env bash
set -e

# Launcher for Global Compliance Intelligence (ComplyIQ)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# If environment is not set up, run setup first
if [ ! -d "backend/.venv" ] || [ ! -d "frontend/node_modules" ]; then
    echo "Running initial setup first..."
    ./setup.sh
fi

VENV_PYTHON="$SCRIPT_DIR/backend/.venv/bin/python3"
UVICORN="$SCRIPT_DIR/backend/.venv/bin/uvicorn"

echo "=========================================================="
echo "  Starting ComplyIQ Platform"
echo "  Backend API:  http://localhost:8000"
echo "  API Docs:     http://localhost:8000/docs"
echo "  Health Check: http://localhost:8000/health"
echo "  Frontend UI:  http://localhost:5173"
echo "=========================================================="
echo "Press Ctrl+C to stop all services."
echo ""

# Trap Ctrl+C (SIGINT) and kill all child processes
trap 'echo ""; echo "Shutting down ComplyIQ services..."; kill $(jobs -p) 2>/dev/null || true; exit 0' SIGINT SIGTERM EXIT

# Start backend
(cd backend && PYTHONPATH=. "$UVICORN" app.main:app --host 0.0.0.0 --port 8000 --reload) &
BACKEND_PID=$!

# Wait briefly for backend to initialize
sleep 2

# Start frontend
(cd frontend && npm run dev -- --host) &
FRONTEND_PID=$!

# Wait for background processes
wait $BACKEND_PID $FRONTEND_PID
