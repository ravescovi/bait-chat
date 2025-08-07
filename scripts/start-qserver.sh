#!/bin/bash
# Start QServer with bAIt-Chat test instrument

set -e

echo "🔬 Starting QServer with test instrument..."
echo "📡 QServer will be available at: http://localhost:60610"

# Get paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_INSTRUMENT_PATH="$PROJECT_ROOT/bait_chat/test_instrument"
QSERVER_PATH="$TEST_INSTRUMENT_PATH/qserver"
QS_SCRIPT="$QSERVER_PATH/qs_host.sh"

# Check if test instrument exists
if [[ ! -f "$QS_SCRIPT" ]]; then
    echo "❌ QServer script not found: $QS_SCRIPT"
    exit 1
fi

# Check dependencies
echo "🔍 Checking dependencies..."
missing=()

if ! python -c "import redis" 2>/dev/null; then
    echo "  ❌ Redis Python client missing"
    missing+=("redis")
fi

if ! python -c "import bluesky_queueserver" 2>/dev/null; then
    echo "  ❌ Bluesky QueueServer missing"
    missing+=("bluesky-queueserver")
fi

if ! python -c "import apsbits" 2>/dev/null; then
    echo "  ❌ APSBITS missing"
    missing+=("apsbits")
fi

if [[ ${#missing[@]} -gt 0 ]]; then
    echo "❌ Missing dependencies: ${missing[*]}"
    echo "Install with: pip install ${missing[*]}"
    exit 1
fi

# Check Redis server
if ! python -c "import redis; r = redis.Redis(); r.ping()" 2>/dev/null; then
    echo "⚠️  Redis server not running. Trying to start..."
    if command -v redis-server >/dev/null; then
        redis-server --daemonize yes
        sleep 2
    else
        echo "❌ Redis server not found. Install with: sudo apt install redis-server"
        exit 1
    fi
fi

# Make script executable and start QServer
chmod +x "$QS_SCRIPT"
cd "$QSERVER_PATH"
exec ./qs_host.sh start "$@"