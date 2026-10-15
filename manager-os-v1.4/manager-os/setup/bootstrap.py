"""Minimal reliable setup, preserving existing credentials, history and local models."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def run(command):
    subprocess.run(command, cwd=ROOT, check=True)


def local_models():
    with urllib.request.urlopen('http://127.0.0.1:11434/api/tags', timeout=3) as response:
        return [m['name'] for m in json.load(response).get('models', [])
                if not any(word in m['name'] for word in ['embed', 'nomic', 'bge-'])]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true', help='Verify runtime without installing or changing accounts')
    args = parser.parse_args()
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))
    if not args.check:
        print('Installing core runtime packages...', flush=True)
        run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements-core.txt'])
    print('Checking application imports...', flush=True)
    run([sys.executable, '-c', 'import main; print("Runtime imports OK")'])
    if args.check:
        try:
            print('Local chat models:', ', '.join(local_models()) or 'none installed')
        except Exception:
            print('Ollama is stopped or not installed. A cloud API key can also be used.')
        return
    for folder in ['logs', 'outputs', 'backups', 'security/identity', 'skills/registry']:
        (ROOT/folder).mkdir(parents=True, exist_ok=True)
    # Playwright uses installed Chrome for automation; Chromium is the fallback.
    chrome = [Path(os.environ.get('PROGRAMFILES', 'C:/Program Files'))/'Google/Chrome/Application/chrome.exe',
              Path(os.environ.get('LOCALAPPDATA', ''))/'Google/Chrome/Application/chrome.exe']
    if not any(p.exists() for p in chrome):
        run([sys.executable, '-m', 'playwright', 'install', 'chromium'])
    ollama = shutil.which('ollama')
    if not ollama:
        candidate = Path(os.environ.get('LOCALAPPDATA', ''))/'Programs/Ollama/ollama.exe'
        if candidate.exists():
            ollama = str(candidate)
    if ollama:
        subprocess.Popen([ollama, 'serve'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        for _ in range(10):
            try:
                models = local_models()
                break
            except Exception:
                time.sleep(1)
        else:
            models = []
        if models:
            print('Using installed local AI:', ', '.join(models))
        else:
            print('Downloading the local chat model (several GB)...', flush=True)
            try:
                run([ollama, 'pull', 'qwen3.5:4b'])
            except subprocess.CalledProcessError:
                print('Local model download did not complete. Use Connections to add a cloud key.')
    else:
        print('Ollama is not installed. Install it for local AI, or add a key in Connections.')
    print('\nSetup complete. Run startup.bat. Create a passphrase in the dashboard on first use.')


if __name__ == '__main__':
    try:
        main()
    except subprocess.CalledProcessError as exc:
        print(f'\nSetup stopped because a required command failed (exit {exc.returncode}). See the error above.')
        raise SystemExit(1)
