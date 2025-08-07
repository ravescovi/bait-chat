#!/bin/bash
# Start bAIt-Chat Streamlit Frontend

set -e

echo "🎨 Starting bAIt-Chat Frontend..."
echo "🌐 Frontend will be available at: http://localhost:8501"

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]] && [[ -z "$CONDA_DEFAULT_ENV" ]]; then
    echo "⚠️  Consider activating a virtual environment first"
fi

# Check if package is installed
if ! python -c "import bait_chat" 2>/dev/null; then
    echo "❌ bait-chat package not found. Installing..."
    pip install -e .[qserver]
fi

# Get the frontend app path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
APP_PATH="$PROJECT_ROOT/bait_chat/frontend/app.py"

# Start frontend
exec streamlit run "$APP_PATH" --server.port 8501 "$@"