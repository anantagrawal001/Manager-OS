"""Stop only the Manager OS process recorded by this checkout's launcher."""
from pathlib import Path
import psutil

ROOT = Path(__file__).resolve().parents[1]
pid_file = ROOT/'logs'/'server.pid'
if not pid_file.exists():
    print('No launched Manager OS process was recorded.')
    raise SystemExit(0)
try:
    process = psutil.Process(int(pid_file.read_text(encoding='ascii').strip()))
    expected = (ROOT/'setup'/'launch.py').resolve()
    scripts = [(Path(process.cwd())/arg).resolve() for arg in process.cmdline()[1:] if arg.endswith('.py')]
    if expected not in scripts:
        raise RuntimeError('Recorded process does not match this Manager OS launcher; no process was stopped.')
    process.terminate()
    process.wait(timeout=10)
    pid_file.unlink(missing_ok=True)
    print('Manager OS stopped. Run startup.bat to reopen it.')
except psutil.NoSuchProcess:
    pid_file.unlink(missing_ok=True)
    print('Manager OS is already stopped.')
