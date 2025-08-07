#!/usr/bin/env python3
"""
QServer startup script for Docker container
"""
import os
import subprocess
import sys
import time
from pathlib import Path


def main():
    """Start QServer in Docker container"""
    print("🔬 Starting QServer in Docker container...")

    # Set up environment
    redis_url = os.environ.get("REDIS_URL", "redis://redis:6379")
    startup_module = os.environ.get("STARTUP_MODULE", "bait_chat.test_instrument.startup")

    print(f"Redis URL: {redis_url}")
    print(f"Startup module: {startup_module}")

    # Wait for Redis to be available
    print("⏳ Waiting for Redis...")
    for i in range(30):
        try:
            import redis

            r = redis.from_url(redis_url, decode_responses=True)
            r.ping()
            print("✅ Redis connected")
            break
        except Exception as e:
            if i == 29:
                print(f"❌ Redis connection failed: {e}")
                sys.exit(1)
            time.sleep(1)

    # Start QServer
    cmd = [
        "start-re-manager",
        "--redis-addr",
        redis_url,
        "--startup-dir",
        str(Path(__file__).parent.parent),
        "--startup-module",
        startup_module,
        "--keep-re",
        "--zmq-publish-console",
        "--verbose",
    ]

    print(f"🚀 Starting QServer: {' '.join(cmd)}")

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ QServer failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
