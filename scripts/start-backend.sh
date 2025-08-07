#!/bin/bash
# Start bAIt-Chat Backend Server

set -e

echo "🚀 Starting bAIt-Chat Backend..."
echo "📡 Backend will be available at: http://localhost:8000"
echo "📚 API Documentation at: http://localhost:8000/docs"

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]] && [[ -z "$CONDA_DEFAULT_ENV" ]]; then
    echo "⚠️  Consider activating a virtual environment first"
fi

# Check if package is installed
if ! python -c "import bait_chat" 2>/dev/null; then
    echo "❌ bait-chat package not found. Installing..."
    pip install -e .[qserver]
fi

# Start backend
exec python -m bait_chat.backend.server "$@"