#!/usr/bin/env python3
"""
bAIt-Chat Demo with Full QServer Integration
Complete demo using the test_instrument BITS setup
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pkg_resources
import requests

print("🔬 bAIt-Chat Demo with QServer Integration")
print("=" * 50)

# Get paths from package
try:
    # Try to get paths from installed package
    package_path = Path(pkg_resources.resource_filename("bait_chat", ""))
    TEST_INSTRUMENT_PATH = package_path / "test_instrument"
    QSERVER_PATH = TEST_INSTRUMENT_PATH / "qserver"
    QSERVER_SCRIPT = QSERVER_PATH / "qs_host.sh"
except:
    # Fallback to current directory
    PROJECT_ROOT = Path(__file__).parent.parent
    TEST_INSTRUMENT_PATH = PROJECT_ROOT / "bait_chat" / "test_instrument"
    QSERVER_PATH = TEST_INSTRUMENT_PATH / "qserver"
    QSERVER_SCRIPT = QSERVER_PATH / "qs_host.sh"

# Process tracking
processes = []
qserver_process = None


def cleanup_processes():
    """Clean up all processes on exit"""
    global processes, qserver_process

    print("\n🛑 Cleaning up processes...")

    # Stop QServer
    if qserver_process:
        try:
            subprocess.run([str(QSERVER_SCRIPT), "stop"], cwd=QSERVER_PATH)
        except:
            pass

    # Stop other processes
    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except:
            try:
                proc.kill()
            except:
                pass

    print("✅ Cleanup complete")


def signal_handler(signum, frame):
    cleanup_processes()
    sys.exit(0)


# Register cleanup handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


def check_dependencies():
    """Check if required dependencies are available"""
    print("🔍 Checking dependencies...")

    missing = []

    # Check Python packages
    try:
        import redis

        print("  ✅ Redis Python client available")
    except ImportError:
        print("  ❌ Redis Python client missing")
        missing.append("redis")

    try:
        import bluesky_queueserver

        print("  ✅ Bluesky QueueServer available")
    except ImportError:
        print("  ❌ Bluesky QueueServer missing")
        missing.append("bluesky-queueserver")

    try:
        import apsbits

        print("  ✅ APSBITS available")
    except ImportError:
        print("  ❌ APSBITS missing")
        missing.append("apsbits")

    # Check Redis server
    try:
        import redis

        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        r.ping()
        print("  ✅ Redis server running")
    except:
        print("  ⚠️  Redis server not running (will try to start)")

    if missing:
        print(f"\n❌ Missing dependencies: {', '.join(missing)}")
        print("Install with: pip install " + " ".join(missing))
        return False

    return True


def start_redis():
    """Start Redis server if not running"""
    try:
        import redis

        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        r.ping()
        print("  ✅ Redis already running")
        return True
    except:
        print("  🚀 Starting Redis server...")
        try:
            redis_proc = subprocess.Popen(["redis-server", "--daemonize", "yes"])
            time.sleep(2)

            r = redis.Redis(host="localhost", port=6379, decode_responses=True)
            r.ping()
            print("  ✅ Redis started successfully")
            return True
        except Exception as e:
            print(f"  ❌ Failed to start Redis: {e}")
            print("  💡 Install Redis: sudo apt install redis-server (Ubuntu/Debian)")
            return False


def start_qserver():
    """Start QServer with the test instrument"""
    global qserver_process

    if not QSERVER_SCRIPT.exists():
        print(f"❌ QServer script not found: {QSERVER_SCRIPT}")
        return False

    print("🚀 Starting QServer with test instrument...")

    try:
        # Make script executable
        os.chmod(QSERVER_SCRIPT, 0o755)

        # Start QServer
        result = subprocess.run(
            [str(QSERVER_SCRIPT), "start"], cwd=QSERVER_PATH, capture_output=True, text=True
        )

        if result.returncode == 0:
            print("  ✅ QServer started")

            # Wait for QServer to be ready
            print("  ⏳ Waiting for QServer to initialize...")
            for i in range(30):
                try:
                    response = requests.get("http://localhost:60610/status", timeout=2)
                    if response.status_code == 200:
                        print("  ✅ QServer is ready!")
                        return True
                except:
                    pass
                time.sleep(1)

            print("  ⚠️  QServer started but may not be fully ready")
            return True
        else:
            print(f"  ❌ Failed to start QServer: {result.stderr}")
            return False

    except Exception as e:
        print(f"  ❌ Error starting QServer: {e}")
        return False


def start_backend():
    """Start the bAIt-Chat backend"""
    print("🚀 Starting bAIt-Chat backend...")

    try:
        backend_proc = subprocess.Popen(
            [sys.executable, "-m", "bait_chat.backend.server"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        processes.append(backend_proc)

        # Wait for backend to start
        time.sleep(3)

        # Test backend
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("  ✅ Backend started successfully")
                return True
        except:
            pass

        print("  ⚠️  Backend started but may not be ready")
        return True

    except Exception as e:
        print(f"  ❌ Error starting backend: {e}")
        return False


def start_frontend():
    """Start the Streamlit frontend"""
    print("🚀 Starting Streamlit frontend...")

    try:
        # Get the frontend app path
        try:
            app_path = pkg_resources.resource_filename("bait_chat.frontend", "app.py")
        except:
            app_path = str(Path(__file__).parent / "frontend" / "app.py")

        frontend_proc = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", app_path, "--server.port", "8501"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )

        processes.append(frontend_proc)

        print("  ✅ Frontend starting...")
        return True

    except Exception as e:
        print(f"  ❌ Error starting frontend: {e}")
        return False


def show_status():
    """Show the status of all services"""
    print("\n📊 Service Status:")

    # Check Redis
    try:
        import redis

        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        r.ping()
        print("  ✅ Redis: Running")
    except:
        print("  ❌ Redis: Not running")

    # Check QServer
    try:
        response = requests.get("http://localhost:60610/status", timeout=2)
        if response.status_code == 200:
            status = response.json()
            print(f"  ✅ QServer: {status.get('manager_state', 'Running')}")
        else:
            print("  ⚠️  QServer: Started but not responding")
    except:
        print("  ❌ QServer: Not running")

    # Check Backend
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("  ✅ Backend: Running")
        else:
            print("  ⚠️  Backend: Not responding")
    except:
        print("  ❌ Backend: Not running")

    # Check Frontend (just assume it's running if process exists)
    frontend_running = any(
        "streamlit" in str(p.args) if hasattr(p, "args") else False for p in processes
    )
    if frontend_running:
        print("  ✅ Frontend: Running")
    else:
        print("  ❌ Frontend: Not running")


def main():
    """Main demo function"""
    try:
        print("🔧 Setting up bAIt-Chat Demo with QServer...")

        # Check dependencies
        if not check_dependencies():
            print("\n❌ Missing dependencies. Please install required packages.")
            return 1

        # Start Redis
        if not start_redis():
            print("\n❌ Redis is required for QServer. Please install and start Redis.")
            return 1

        # Start QServer
        if not start_qserver():
            print("\n❌ Failed to start QServer")
            return 1

        # Start Backend
        if not start_backend():
            print("\n❌ Failed to start backend")
            return 1

        # Start Frontend
        if not start_frontend():
            print("\n❌ Failed to start frontend")
            return 1

        # Show status
        time.sleep(2)
        show_status()

        print("\n🎉 bAIt-Chat Demo is now running!")
        print("=" * 50)
        print("🌐 Access the application:")
        print("   Frontend:    http://localhost:8501")
        print("   Backend API: http://localhost:8000")
        print("   API Docs:    http://localhost:8000/docs")
        print("   QServer:     http://localhost:60610")
        print("")
        print("📋 Available devices and plans loaded from test_instrument:")
        print("   - Simulated motors and detectors")
        print("   - Standard Bluesky scan plans")
        print("   - Real QServer integration")
        print("")
        print("💬 Try asking the AI:")
        print('   - "What devices are available?"')
        print('   - "Explain the scan plan"')
        print('   - "How do I run a grid scan?"')
        print("")
        print("🛑 Press Ctrl+C to stop all services")

        # Keep running until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

    except KeyboardInterrupt:
        pass
    finally:
        cleanup_processes()

    return 0


if __name__ == "__main__":
    sys.exit(main())
