#!/usr/bin/env python3
"""One-click launcher for ProjectPilot on Windows/macOS/Linux."""
from __future__ import annotations
import os
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
HOST = "127.0.0.1"
PORT = 8000
URL = f"http://{HOST}:{PORT}"


def port_open(host: str, port: int) -> bool:
    with socket.socket() as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((host, port)) == 0


def healthy() -> bool:
    try:
        with urllib.request.urlopen(URL + "/api/", timeout=1.0) as response:
            return response.status == 200
    except Exception:
        return False


def main() -> int:
    if port_open(HOST, PORT):
        if healthy():
            print(f"ProjectPilot is already running at {URL}")
            webbrowser.open(URL)
            return 0
        print(f"Port {PORT} is already in use by another program.")
        input("Press Enter to close...")
        return 1

    cmd = [sys.executable, str(ROOT / "run.py")]
    print("Starting ProjectPilot. The first start can take a few minutes while Python packages install.")
    proc = subprocess.Popen(cmd, cwd=ROOT)
    opened = False
    try:
        deadline = time.time() + 600
        while time.time() < deadline:
            if proc.poll() is not None:
                print(f"ProjectPilot stopped before it became ready (exit code {proc.returncode}).")
                input("Press Enter to close...")
                return proc.returncode or 1
            if healthy():
                print(f"ProjectPilot is ready: {URL}")
                webbrowser.open(URL)
                opened = True
                break
            time.sleep(1)
        if not opened:
            print("ProjectPilot did not become ready within 10 minutes.")
            proc.terminate()
            input("Press Enter to close...")
            return 1
        return proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
