#!/bin/bash
# Start all bAIt-Chat services with Docker Compose

set -e

echo "🐳 Starting bAIt-Chat with Docker Compose"
echo "========================================"

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose >/dev/null && ! command -v docker >/dev/null; then
    echo "❌ Docker Compose is not available"
    exit 1
fi

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Build and start services
echo "🔨 Building and starting services..."
if command -v docker-compose >/dev/null; then
    docker-compose up --build -d
else
    docker compose up --build -d
fi

echo ""
echo "⏳ Waiting for services to be ready..."

# Wait for services
services=("redis:6379" "qserver:60610" "backend:8000" "frontend:8501")
for service in "${services[@]}"; do
    service_name="${service%:*}"
    port="${service#*:}"
    echo "  Checking $service_name..."
    
    for i in {1..30}; do
        if curl -s "http://localhost:$port" >/dev/null 2>&1; then
            echo "    ✅ $service_name ready"
            break
        fi
        if [[ $i -eq 30 ]]; then
            echo "    ⚠️  $service_name timeout"
        fi
        sleep 2
    done
done

echo ""
echo "🎉 bAIt-Chat is running in Docker!"
echo "================================"
echo "🌐 Access the application:"
echo "   Frontend:    http://localhost:8501"
echo "   Backend API: http://localhost:8000"
echo "   API Docs:    http://localhost:8000/docs"
echo "   QServer:     http://localhost:60610"
echo ""
echo "📋 Docker services:"
if command -v docker-compose >/dev/null; then
    docker-compose ps
else
    docker compose ps
fi
echo ""
echo "🛑 Stop services with: scripts/docker-down.sh"