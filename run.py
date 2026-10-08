#!/usr/bin/env python3
"""Start ProjectPilot locally. Bundled frontend; no Node build required to open the app."""
import argparse
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import venv

ROOT=Path(__file__).resolve().parent

def main():
    parser=argparse.ArgumentParser(description='ProjectPilot local workspace')
    parser.add_argument('--check',action='store_true',help='Print prerequisites without installing or starting anything')
    parser.add_argument('--port',type=int,default=8000)
    parser.add_argument('--no-install',action='store_true',help='Require an existing virtual environment')
    args=parser.parse_args()
    py=ROOT/'.venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    if args.check:
        print('Python:',sys.version.split()[0]);print('Git:',shutil.which('git') or 'MISSING (required)');print('Node:',shutil.which('node') or 'optional; required for JavaScript syntax checks');print('Docker:',shutil.which('docker') or 'optional; required for isolated build commands');print('Bundled frontend:',(ROOT/'frontend/dist/index.html').is_file());print('Virtual environment:',py.is_file());return
    if sys.version_info<(3,11): raise SystemExit('Install Python 3.11 or newer.')
    if not shutil.which('git'): raise SystemExit('Install Git, reopen your terminal, and run this command again.')
    if not (ROOT/'frontend/dist/index.html').is_file(): raise SystemExit('Frontend bundle missing. In frontend run: npm ci, then npm run build.')
    if not py.exists():
        if args.no_install: raise SystemExit('No virtual environment. Run without --no-install to set it up.')
        print('Creating a local Python environment and installing pinned dependencies…',flush=True)
        venv.EnvBuilder(with_pip=True).create(ROOT/'.venv')
        subprocess.run([str(py),'-m','pip','install','-r',str(ROOT/'backend/requirements.txt')],check=True)
    check=subprocess.run([str(py),'-c','import fastapi,uvicorn,httpx,dotenv,pydantic'],capture_output=True)
    if check.returncode:
        if args.no_install: raise SystemExit('Python dependencies missing.')
        subprocess.run([str(py),'-m','pip','install','-r',str(ROOT/'backend/requirements.txt')],check=True)
    print(f'Open http://127.0.0.1:{args.port} — press Ctrl+C to stop.',flush=True)
    # Exactly one worker. Bind to loopback; remote hosting needs a separate deployment design.
    try: subprocess.run([str(py),'-m','uvicorn','server:app','--app-dir',str(ROOT/'backend'),'--host','127.0.0.1','--port',str(args.port),'--workers','1'],cwd=ROOT,check=True)
    except KeyboardInterrupt: pass

if __name__=='__main__': main()
