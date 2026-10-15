"""Double-click launcher: reuse a running server or start it in this folder."""
import os
from pathlib import Path
import runpy
import sys
import urllib.request
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))


def main():
    try:
        import yaml
        with open('config.yaml', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
        port = int(config.get('server', {}).get('port', 8000))
        url = f'http://127.0.0.1:{port}'
        try:
            import json
            with urllib.request.urlopen(url + '/api/health', timeout=2) as response:
                data = json.load(response)
            if data.get('ready'):
                print('Manager OS is already running. Opening the dashboard.')
                webbrowser.open(url)
                return
        except Exception:
            pass
        import main as server
        import uvicorn
        pid_file = ROOT/'logs'/'server.pid'
        pid_file.parent.mkdir(parents=True, exist_ok=True)
        pid_file.write_text(str(os.getpid()), encoding='ascii')
        try:
            uvicorn.run(server.app, host='127.0.0.1', port=port, log_level='info')
        finally:
            if pid_file.exists() and pid_file.read_text(encoding='ascii').strip() == str(os.getpid()):
                pid_file.unlink()
    except ImportError as exc:
        print(f'A required package is missing ({exc.name}). Run SETUP.bat first.')
        raise SystemExit(1)


if __name__ == '__main__':
    main()
