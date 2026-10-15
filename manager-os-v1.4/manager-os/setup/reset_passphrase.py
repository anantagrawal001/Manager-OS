"""Local-only recovery: retire the login hash without changing vault keys or data."""
from datetime import datetime, timezone
from pathlib import Path
import socket
import subprocess
import sys
import uuid


def retire_passphrase(root):
    identity = Path(root) / 'security' / 'identity'
    current = identity / 'passphrase.hash'
    if not current.exists():
        return None
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup = identity / f'passphrase-reset-{stamp}-{uuid.uuid4().hex[:8]}.hash.bak'
    current.rename(backup)
    return backup


def main():
    import yaml
    root = Path(__file__).resolve().parents[1]
    subprocess.run([sys.executable, str(root / 'setup' / 'stop.py')], cwd=root, check=True)
    config = yaml.safe_load((root / 'config.yaml').read_text(encoding='utf-8')) or {}
    port = int(config.get('server', {}).get('port', 8000))
    for candidate in {8000, port}:
        with socket.socket() as probe:
            probe.settimeout(1)
            if probe.connect_ex(('127.0.0.1', candidate)) == 0:
                raise RuntimeError('A server is still listening. Stop Manager OS before resetting its passphrase.')
    retire_passphrase(root)
    print('Login reset. Your vault keys, history and tasks are unchanged.')
    print('Run startup.bat, refresh the dashboard, and create a new passphrase.')


if __name__ == '__main__':
    main()
