#!/usr/bin/env bash
set -e

# Setup script for Global Compliance Intelligence (ComplyIQ)
# Designed for Linux/macOS environments

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=========================================================="
echo "  Setting up Global Compliance Intelligence (ComplyIQ)"
echo "=========================================================="

# 1. Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "Error: python3 is required but not installed." >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Error: node is required but not installed." >&2; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "Error: npm is required but not installed." >&2; exit 1; }

echo "✓ Python: $(python3 --version)"
echo "✓ Node:   $(node -v)"
echo "✓ npm:    $(npm -v)"

# 2. Setup .env file
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# 3. Setup Python virtual environment
VENV_PATH="$SCRIPT_DIR/backend/.venv"
if [ ! -d "$VENV_PATH" ]; then
    echo "Creating virtual environment at $VENV_PATH..."
    python3 -m venv --system-site-packages "$VENV_PATH" 2>/dev/null || python3 -m venv "$VENV_PATH"
fi

echo "Installing backend Python dependencies..."
"$VENV_PATH/bin/pip" install --upgrade pip >/dev/null 2>&1 || true
"$VENV_PATH/bin/pip" install pysqlite3-binary -q 2>/dev/null || true
"$VENV_PATH/bin/pip" install -r backend/requirements.txt -q

# 4. Run database migrations
echo "Running database migrations..."
(cd backend && PYTHONPATH=. "$VENV_PATH/bin/alembic" upgrade head)

# 5. Install frontend dependencies
echo "Installing frontend dependencies..."
(cd frontend && npm install --silent)

# 6. Ensure data directories exist and sync vectors
mkdir -p data/uploads data/qdrant data/company/g-inc/uploads data/legal/india/dpdp data/legal/india/it_act
"$VENV_PATH/bin/python3" scripts/sync_vectors.py

echo "=========================================================="
echo "  Setup completed successfully!"
echo "  Run ./start.sh to launch both Backend and Frontend."
echo "=========================================================="
