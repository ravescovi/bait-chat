#!/bin/bash
# Start full bAIt-Chat demo with all services

set -e

# Activate conda environment 'bits'
if command -v conda >/dev/null 2>&1; then
    echo "🐍 Activating conda environment 'bits'..."
    eval "$(conda shell.bash hook)"
    conda activate bits || {
        echo "❌ Failed to activate conda environment 'bits'"
        echo "   Please ensure the 'bits' environment exists"
        echo "   Create it with: conda create -n bits python=3.10"
        exit 1
    }
    echo "  ✅ Conda environment 'bits' activated"
else
    echo "⚠️  Conda not found, using system Python"
fi

echo "🔬 bAIt-Chat Full Demo Startup"
echo "============================="

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Process tracking
pids=()
qserver_started=false

cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    
    # Stop QServer
    if [[ "$qserver_started" == "true" ]]; then
        echo "  Stopping QServer..."
        "$SCRIPT_DIR/stop-qserver.sh" || true
    fi
    
    # Kill other processes
    for pid in "${pids[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "  Stopping process $pid..."
            kill "$pid" 2>/dev/null || true
        fi
    done
    
    # Wait for processes to stop
    sleep 2
    for pid in "${pids[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            echo "  Force killing process $pid..."
            kill -9 "$pid" 2>/dev/null || true
        fi
    done
    
    echo "✅ Cleanup complete"
}

# Setup signal handlers
trap cleanup EXIT
trap cleanup INT
trap cleanup TERM

# Check and install dependencies if needed
echo "📦 Checking Python dependencies..."
missing_deps=()

if ! python -c "import redis" 2>/dev/null; then
    missing_deps+=("redis")
fi

if ! python -c "import bluesky_queueserver" 2>/dev/null; then
    missing_deps+=("bluesky-queueserver")
fi

if ! python -c "import apsbits" 2>/dev/null; then
    missing_deps+=("apsbits")
fi

if ! python -c "import fastapi" 2>/dev/null; then
    missing_deps+=("fastapi")
fi

if ! python -c "import uvicorn" 2>/dev/null; then
    missing_deps+=("uvicorn[standard]")
fi

if ! python -c "import streamlit" 2>/dev/null; then
    missing_deps+=("streamlit")
fi

if [[ ${#missing_deps[@]} -gt 0 ]]; then
    echo "  📥 Installing missing dependencies: ${missing_deps[*]}"
    pip install ${missing_deps[*]} || {
        echo "  ⚠️  Some dependencies failed to install, continuing anyway..."
    }
else
    echo "  ✅ All Python dependencies installed"
fi

# Start Redis if needed
echo "🔍 Checking Redis..."
if ! python -c "import redis; r = redis.Redis(); r.ping()" 2>/dev/null; then
    echo "  Starting Redis..."
    if command -v redis-server >/dev/null; then
        redis-server --daemonize yes
        sleep 2
    else
        echo "❌ Redis server not found. Install with: sudo apt install redis-server"
        exit 1
    fi
fi
echo "  ✅ Redis running"

# Start QServer
echo "🔬 Starting QServer..."
"$SCRIPT_DIR/start-qserver.sh" &
qserver_started=true
echo "  ⏳ Waiting for QServer to initialize..."
for i in {1..30}; do
    if curl -s http://localhost:60610/status >/dev/null 2>&1; then
        echo "  ✅ QServer ready"
        break
    fi
    if [[ $i -eq 30 ]]; then
        echo "  ⚠️  QServer timeout, but continuing..."
    fi
    sleep 1
done

# Start Backend
echo "🚀 Starting Backend..."
"$SCRIPT_DIR/start-backend.sh" &
backend_pid=$!
pids+=($backend_pid)
echo "  ⏳ Waiting for Backend to start..."
for i in {1..15}; do
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        echo "  ✅ Backend ready"
        break
    fi
    if [[ $i -eq 15 ]]; then
        echo "  ⚠️  Backend timeout, but continuing..."
    fi
    sleep 1
done

# Start Frontend
echo "🎨 Starting Frontend..."
"$SCRIPT_DIR/start-frontend.sh" &
frontend_pid=$!
pids+=($frontend_pid)
echo "  ✅ Frontend starting..."

# Wait a bit for everything to stabilize
sleep 3

echo ""
echo "🎉 bAIt-Chat Demo is now running!"
echo "============================="
echo "🌐 Access the application:"
echo "   Frontend:    http://localhost:8501"
echo "   Backend API: http://localhost:8000"
echo "   API Docs:    http://localhost:8000/docs"
echo "   QServer:     http://localhost:60610"
echo ""
echo "📋 Available devices and plans loaded from test_instrument"
echo "💬 Try asking the AI:"
echo '   - "What devices are available?"'
echo '   - "Explain the scan plan"'
echo '   - "How do I run a grid scan?"'
echo ""
echo "🛑 Press Ctrl+C to stop all services"

# Keep running until interrupted
wait