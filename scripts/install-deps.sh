#!/bin/bash
# Install bAIt-Chat dependencies

set -e

echo "📦 Installing bAIt-Chat Dependencies"
echo "==================================="

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "🐍 Python version: $python_version"

if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
    echo "  ✅ Python version OK"
else
    echo "  ❌ Python 3.8+ required"
    exit 1
fi

# Install system dependencies
echo "🔧 Checking system dependencies..."
if command -v apt-get >/dev/null; then
    echo "  Installing Redis via apt..."
    sudo apt-get update
    sudo apt-get install -y redis-server
elif command -v brew >/dev/null; then
    echo "  Installing Redis via Homebrew..."
    brew install redis
    brew services start redis
else
    echo "  ⚠️  Please install Redis manually for your system"
fi

# Install Python package
echo "📦 Installing bAIt-Chat package..."
pip install -e .[qserver]

echo ""
echo "✅ Installation complete!"
echo ""
echo "🚀 Quick start:"
echo "   scripts/demo.sh           # Full demo"
echo "   scripts/start-backend.sh  # Backend only"
echo "   scripts/start-frontend.sh # Frontend only"