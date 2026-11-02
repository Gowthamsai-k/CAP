#!/usr/bin/env bash
set -e

# Setup script for Global Compliance Intelligence (ComplyIQ)
# Uses `uv` for ultra-fast Python environment/dependencies and `npm` for frontend

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

echo "=========================================================="
echo "  Setting up Global Compliance Intelligence (ComplyIQ)"
echo "=========================================================="

# 1. Check Node and npm
command -v node >/dev/null 2>&1 || { echo "Error: node is required but not installed." >&2; exit 1; }
command -v npm >/dev/null 2>&1 || { echo "Error: npm is required but not installed." >&2; exit 1; }
echo "✓ Node:   $(node -v)"
echo "✓ npm:    $(npm -v)"

# 2. Check or install uv
if ! command -v uv >/dev/null 2>&1; then
    echo "uv not found. Installing uv (fast Python package manager)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh || true
    export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

if command -v uv >/dev/null 2>&1; then
    echo "✓ uv:     $(uv --version)"
    USE_UV=1
else
    echo "Warning: uv could not be installed automatically; falling back to python3 venv/pip."
    command -v python3 >/dev/null 2>&1 || { echo "Error: python3 is required." >&2; exit 1; }
    echo "✓ Python: $(python3 --version)"
    USE_UV=0
fi

# 3. Setup .env file
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# 4. Setup Python virtual environment & dependencies
VENV_PATH="$SCRIPT_DIR/backend/.venv"
VENV_PYTHON="$VENV_PATH/bin/python3"

if [ "$USE_UV" -eq 1 ]; then
    if [ ! -d "$VENV_PATH" ]; then
        echo "Creating virtual environment with uv at $VENV_PATH..."
        uv venv --system-site-packages "$VENV_PATH" 2>/dev/null || uv venv "$VENV_PATH"
    fi
    echo "Installing backend dependencies with uv..."
    VIRTUAL_ENV="$VENV_PATH" uv pip install pysqlite3-binary -r backend/requirements.txt
else
    if [ ! -d "$VENV_PATH" ]; then
        echo "Creating virtual environment at $VENV_PATH..."
        python3 -m venv --system-site-packages "$VENV_PATH" 2>/dev/null || python3 -m venv "$VENV_PATH"
    fi
    echo "Installing backend dependencies with pip..."
    "$VENV_PATH/bin/pip" install --upgrade pip >/dev/null 2>&1 || true
    "$VENV_PATH/bin/pip" install pysqlite3-binary -r backend/requirements.txt
fi

# 5. Run database migrations
echo "Running database migrations..."
(cd backend && PYTHONPATH=. "$VENV_PATH/bin/alembic" upgrade head)

# 6. Install frontend dependencies using npm
echo "Installing frontend dependencies using npm..."
(cd frontend && npm install)

# 7. Ensure data directories exist and sync vectors
mkdir -p data/uploads data/qdrant data/company/g-inc/uploads data/legal/india/dpdp data/legal/india/it_act
"$VENV_PYTHON" scripts/sync_vectors.py

echo "=========================================================="
echo "  Setup completed successfully!"
echo "  Run ./start.sh to launch both Backend and Frontend."
echo "=========================================================="
