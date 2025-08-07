#!/bin/bash
# Stop QServer

set -e

echo "🛑 Stopping QServer..."

# Get paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_INSTRUMENT_PATH="$PROJECT_ROOT/src/demo_instrument"
QSERVER_PATH="$TEST_INSTRUMENT_PATH/qserver"
QS_SCRIPT="$QSERVER_PATH/qs_host.sh"

# Check if test instrument exists
if [[ ! -f "$QS_SCRIPT" ]]; then
    echo "❌ QServer script not found: $QS_SCRIPT"
    exit 1
fi

# Stop QServer
chmod +x "$QS_SCRIPT"
cd "$QSERVER_PATH"
exec ./qs_host.sh stop "$@"