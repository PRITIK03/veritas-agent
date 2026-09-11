#!/usr/bin/env python3
"""
Simple run script for Veritas Agent.
Usage: python run.py
"""

import subprocess
import sys
import os
import socket
import webbrowser
import time
from pathlib import Path

ROOT = Path(__file__).parent
VENV_PYTHON = ROOT / "venv" / "Scripts" / "python.exe"

def is_port_free(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(("127.0.0.1", port)) != 0
    except:
        return False

def find_free_port(start=8000):
    for port in range(start, start + 10):
        if is_port_free(port):
            return port
    return None

def main():
    print("=" * 50)
    print("  Veritas Agent - Starting up")
    print("=" * 50)

    # Check venv
    if not VENV_PYTHON.exists():
        print("❌ Virtual environment not found at:", VENV_PYTHON)
        print("   Run: python -m venv venv && venv\\Scripts\\activate && pip install -r requirements.txt")
        return 1

    # Check .env
    env_file = ROOT / ".env"
    if not env_file.exists():
        print("⚠️  .env not found. Copy .env.example to .env and fill in your keys.")
        example = ROOT / ".env.example"
        if example.exists():
            import shutil
            shutil.copy(example, env_file)
            print("   Copied .env.example -> .env (please edit it)")

    # Find port
    port = find_free_port(8000)
    if port is None:
        print("❌ No free ports in range 8000-8009")
        return 1
    elif port != 8000:
        print(f"⚠️  Port 8000 busy, using {port}")

    print(f"🚀 Starting server on http://localhost:{port}")
    print("   Press Ctrl+C to stop")
    print()

    # Start uvicorn
    cmd = [
        str(VENV_PYTHON), "-m", "uvicorn",
        "app.main:app",
        "--port", str(port),
        "--host", "127.0.0.1",
    ]

    # Give server time to start, then open browser
    def open_browser():
        time.sleep(2.5)
        webbrowser.open(f"http://localhost:{port}")

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    try:
        subprocess.run(cmd, cwd=ROOT)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

if __name__ == "__main__":
    sys.exit(main())