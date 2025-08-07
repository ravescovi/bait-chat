#!/bin/bash
# Stop all bAIt-Chat services with Docker Compose

set -e

echo "🛑 Stopping bAIt-Chat Docker services..."

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Stop services
if command -v docker-compose >/dev/null; then
    docker-compose down "$@"
else
    docker compose down "$@"
fi

echo "✅ Services stopped"

# Show usage options
echo ""
echo "💡 Options:"
echo "   scripts/docker-down.sh -v    # Remove volumes (data will be lost)"
echo "   scripts/docker-up.sh         # Start services again"