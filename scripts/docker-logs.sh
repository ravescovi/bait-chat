#!/bin/bash
# View logs from bAIt-Chat Docker services

set -e

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Show logs
if [[ $# -eq 0 ]]; then
    echo "📋 Showing logs for all services..."
    if command -v docker-compose >/dev/null; then
        docker-compose logs -f
    else
        docker compose logs -f
    fi
else
    service="$1"
    echo "📋 Showing logs for $service..."
    if command -v docker-compose >/dev/null; then
        docker-compose logs -f "$service"
    else
        docker compose logs -f "$service"
    fi
fi