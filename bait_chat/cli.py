"""
Command-line interface for bAIt-Chat
"""

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def signal_handler(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n🛑 Shutting down bAIt-Chat...")
    sys.exit(0)


def start_demo():
    """Start the full demo with QServer"""
    from .demo import main as demo_main

    return demo_main()


def start_backend():
    """Start just the backend server"""
    from .backend.server import main as backend_main

    return backend_main()


def start_frontend():
    """Start just the frontend"""
    from .frontend.app import main as frontend_main

    return frontend_main()


def install_demo_deps():
    """Install dependencies for the demo"""
    print("📦 Installing demo dependencies...")

    try:
        # Install the package with QServer extras
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", ".[qserver,all]"], check=True)

        print("✅ Dependencies installed successfully!")
        print("🚀 Ready to run: bait-chat demo")
        return 0

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return 1


def show_status():
    """Show status of bAIt-Chat services"""
    import requests

    services = [
        ("Backend", "http://localhost:8000/health"),
        ("QServer", "http://localhost:60610/status"),
        ("Frontend", "http://localhost:8501"),
        ("Redis", None),  # Special case for Redis
    ]

    print("📊 bAIt-Chat Service Status:")
    print("-" * 30)

    for service_name, url in services:
        if service_name == "Redis":
            # Check Redis separately
            try:
                import redis

                r = redis.Redis(host="localhost", port=6379, decode_responses=True)
                r.ping()
                print(f"  ✅ {service_name}: Running")
            except:
                print(f"  ❌ {service_name}: Not running")
        else:
            try:
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    print(f"  ✅ {service_name}: Running")
                else:
                    print(f"  ⚠️  {service_name}: Responding but with errors")
            except:
                print(f"  ❌ {service_name}: Not running")


def main():
    """Main CLI entry point"""
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser(
        prog="bait-chat",
        description="bAIt-Chat: AI assistant for Bluesky beamline control",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  bait-chat demo              # Start full demo with QServer
  bait-chat backend           # Start backend only  
  bait-chat frontend          # Start frontend only
  bait-chat install-deps      # Install demo dependencies
  bait-chat status            # Check service status
        """,
    )

    parser.add_argument(
        "command",
        choices=["demo", "backend", "frontend", "install-deps", "status"],
        help="Command to execute",
    )

    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")

    parser.add_argument(
        "--port", type=int, help="Port to bind to (default: 8000 for backend, 8501 for frontend)"
    )

    parser.add_argument(
        "--qserver-url",
        default="http://localhost:60610",
        help="QServer URL (default: http://localhost:60610)",
    )

    parser.add_argument(
        "--lmstudio-url",
        default="http://127.0.0.1:1234",
        help="LMStudio URL (default: http://127.0.0.1:1234)",
    )

    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    if len(sys.argv) == 1:
        parser.print_help()
        return 0

    args = parser.parse_args()

    # Set environment variables from args
    os.environ["QSERVER_URL"] = args.qserver_url
    os.environ["LMSTUDIO_URL"] = args.lmstudio_url

    if args.debug:
        os.environ["DEBUG"] = "1"

    # Execute commands
    if args.command == "demo":
        return start_demo()
    elif args.command == "backend":
        return start_backend()
    elif args.command == "frontend":
        return start_frontend()
    elif args.command == "install-deps":
        return install_demo_deps()
    elif args.command == "status":
        show_status()
        return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
