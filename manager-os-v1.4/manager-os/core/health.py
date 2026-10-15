"""
MANAGER OS — Health Agent (Full System Monitor)
FILE: core/health.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
UPDATED: 2026-05-28 | Claude Sonnet 4.6
CHANGES:
  - RAM alert threshold raised to 95% (was 90%) [2026-05-28]
  - Alert cooldown: 10 min per alert type (was no cooldown) [2026-05-28]
  - Edge TTS 403 errors silenced — known issue, fall to pyttsx3 [2026-05-28]
  - Hardware monitoring every 60s, software every 30s
  - Log rotation enforcement every hour
DO NOT DELETE ANY CODE — comment out with reason and date
"""

import asyncio
import platform
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field

import psutil
from loguru import logger


@dataclass
class AgentStatus:
    name: str
    healthy: bool = True
    state: str = "running"
    last_check: datetime = field(default_factory=datetime.now)
    last_success: datetime = field(default_factory=datetime.now)
    fail_count: int = 0
    last_error: Optional[str] = None
    restart_count: int = 0


@dataclass
class HardwareSnapshot:
    timestamp: datetime
    cpu_pct: float
    cpu_temp: Optional[float]
    ram_used_gb: float
    ram_total_gb: float
    ram_pct: float
    gpu_pct: Optional[float]
    gpu_vram_used_gb: Optional[float]
    disk_free_gb: float
    disk_total_gb: float
    network_sent_mbps: float
    network_recv_mbps: float


class HealthAgent:
    SOFTWARE_CHECK_INTERVAL = 30
    HARDWARE_CHECK_INTERVAL = 60
    LOG_CHECK_INTERVAL = 3600

    # OLD (2026-05-27): MAX_RAM_PCT = 90.0 — too sensitive, fired every 3 min
    # NEW (2026-05-28): raised to 95% — 16GB with AI models always runs high
    MAX_CPU_PCT = 92.0
    MAX_RAM_PCT = 95.0
    MIN_DISK_FREE_GB = 15.0
    MAX_CPU_TEMP = 90.0

    # NEW (2026-05-28): Alert cooldown — same alert won't fire within 10 minutes
    ALERT_COOLDOWN_SECONDS = 600
    MAX_FAIL_BEFORE_NOTIFY = 3
    LOG_CAP_BYTES = 5 * 1024 * 1024 * 1024  # 5GB

    def __init__(self, config: dict):
        self.config = config
        self.agents: Dict[str, Any] = {}
        self.statuses: Dict[str, AgentStatus] = {}
        self.hardware_history: List[HardwareSnapshot] = []
        self.running = False
        self.notify_callback: Optional[Callable] = None
        self._tasks: List[asyncio.Task] = []
        counters = psutil.net_io_counters()
        self._prev_net_sent = counters.bytes_sent
        self._prev_net_recv = counters.bytes_recv
        self._prev_net_time = time.time()
        # NEW: cooldown tracker per alert type
        self._last_alert_time: Dict[str, float] = {}

    def set_notify_callback(self, callback: Callable):
        self.notify_callback = callback

    async def start_monitoring(self, agents: Dict[str, Any]):
        self.agents = agents
        self.running = True
        for name in agents:
            self.statuses[name] = AgentStatus(name=name)
        self._tasks = [
            asyncio.create_task(self._software_loop()),
            asyncio.create_task(self._hardware_loop()),
            asyncio.create_task(self._log_size_loop()),
        ]
        logger.info(f"Health agent started — monitoring {len(agents)} agents + hardware + logs")

    async def _software_loop(self):
        while self.running:
            await self._check_all_agents()
            await self._check_system_services()
            await asyncio.sleep(self.SOFTWARE_CHECK_INTERVAL)

    async def _check_all_agents(self):
        for name, agent in self.agents.items():
            try:
                await self._check_agent(name, agent)
            except Exception as e:
                logger.error(f"Check error {name}: {e}")

    async def _check_agent(self, name: str, agent: Any):
        status = self.statuses.setdefault(name, AgentStatus(name=name))
        try:
            if hasattr(agent, "get_status"):
                fn = agent.get_status
                if asyncio.iscoroutinefunction(fn):
                    result = await asyncio.wait_for(fn(), timeout=10.0)
                else:
                    result = fn()
                is_healthy = result.get("healthy", True) if isinstance(result, dict) else bool(result)
            else:
                is_healthy = agent is not None

            if is_healthy:
                status.healthy = True
                status.state = "running"
                status.last_success = datetime.now()
                status.fail_count = 0
            else:
                await self._handle_unhealthy(name, agent, status, "Agent reported unhealthy")
        except asyncio.TimeoutError:
            await self._handle_unhealthy(name, agent, status, "Health check timed out")
        except Exception as e:
            await self._handle_unhealthy(name, agent, status, str(e))

    async def _check_system_services(self):
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as c:
                r = await c.get("http://localhost:11434/api/tags")
                if r.status_code != 200:
                    await self._attempt_start_ollama()
        except Exception:
            await self._attempt_start_ollama()

    async def _attempt_start_ollama(self):
        import subprocess
        try:
            kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
            if platform.system() == "Windows":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            subprocess.Popen(["ollama", "serve"], **kwargs)
            logger.info("Health Agent: Ollama restarted automatically")
        except Exception as e:
            await self._notify_sir_throttled(
                "ollama_down",
                "Sir, the local AI (Ollama) stopped and I couldn't restart it automatically. "
                "Please open a terminal and run: ollama serve"
            )

    async def _handle_unhealthy(self, name: str, agent: Any, status: AgentStatus, error: str):
        status.healthy = False
        status.fail_count += 1
        status.last_error = error
        status.last_check = datetime.now()
        logger.warning(f"Agent {name} unhealthy (fail #{status.fail_count}): {error}")
        if status.fail_count <= 3:
            await self._restart_agent(name, agent, status)
        if status.fail_count >= self.MAX_FAIL_BEFORE_NOTIFY:
            await self._notify_sir_throttled(
                f"agent_{name}",
                f"Sir, the {name} agent has failed {status.fail_count} times and I can't fix it. "
                f"Error: {error[:100]}. Everything else is running normally."
            )

    async def _restart_agent(self, name: str, agent: Any, status: AgentStatus):
        status.state = "restarting"
        status.restart_count += 1
        try:
            if hasattr(agent, "restart"):
                await agent.restart()
            elif hasattr(agent, "initialize"):
                await agent.initialize()
            status.healthy = True
            status.state = "running"
            status.fail_count = 0
            logger.info(f"Agent {name} restarted successfully")
        except Exception as e:
            logger.error(f"Restart failed {name}: {e}")
            status.state = "failed"

    async def _hardware_loop(self):
        while self.running:
            snap = await asyncio.to_thread(self._capture_hardware)
            if snap:
                self.hardware_history.append(snap)
                if len(self.hardware_history) > 1440:
                    self.hardware_history = self.hardware_history[-1440:]
                await self._check_hardware_alerts(snap)
            await asyncio.sleep(self.HARDWARE_CHECK_INTERVAL)

    def _capture_hardware(self) -> Optional[HardwareSnapshot]:
        try:
            cpu_pct = psutil.cpu_percent(interval=1)
            cpu_temp = None
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    for entries in temps.values():
                        if entries:
                            cpu_temp = entries[0].current
                            break
            except Exception:
                pass

            ram = psutil.virtual_memory()
            disk_path = "C:\\" if platform.system() == "Windows" else "/"
            disk = psutil.disk_usage(disk_path)
            net = psutil.net_io_counters()
            now = time.time()
            elapsed = max(now - self._prev_net_time, 0.001)
            sent_mbps = (net.bytes_sent - self._prev_net_sent) / (1024**2) / elapsed
            recv_mbps = (net.bytes_recv - self._prev_net_recv) / (1024**2) / elapsed
            self._prev_net_sent = net.bytes_sent
            self._prev_net_recv = net.bytes_recv
            self._prev_net_time = now

            gpu_pct, gpu_vram = None, None
            try:
                import subprocess
                r = subprocess.run(
                    ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used",
                     "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=5
                )
                if r.returncode == 0:
                    parts = r.stdout.strip().split(", ")
                    if len(parts) >= 2:
                        gpu_pct = float(parts[0])
                        gpu_vram = float(parts[1]) / 1024
            except Exception:
                pass

            return HardwareSnapshot(
                timestamp=datetime.now(),
                cpu_pct=cpu_pct, cpu_temp=cpu_temp,
                ram_used_gb=round(ram.used / 1024**3, 2),
                ram_total_gb=round(ram.total / 1024**3, 2),
                ram_pct=ram.percent,
                gpu_pct=gpu_pct,
                gpu_vram_used_gb=round(gpu_vram, 2) if gpu_vram else None,
                disk_free_gb=round(disk.free / 1024**3, 2),
                disk_total_gb=round(disk.total / 1024**3, 2),
                network_sent_mbps=round(sent_mbps, 2),
                network_recv_mbps=round(recv_mbps, 2),
            )
        except Exception as e:
            logger.error(f"Hardware capture error: {e}")
            return None

    async def _check_hardware_alerts(self, snap: HardwareSnapshot):
        """Check hardware metrics — with cooldown to prevent alert spam"""
        if snap.cpu_pct > self.MAX_CPU_PCT:
            await self._notify_sir_throttled(
                "cpu_high",
                f"Sir, CPU is at {snap.cpu_pct:.0f}% — system under heavy load."
            )
        if snap.cpu_temp and snap.cpu_temp > self.MAX_CPU_TEMP:
            await self._notify_sir_throttled(
                "cpu_temp",
                f"Sir, CPU temperature {snap.cpu_temp:.0f}°C — please ensure ventilation."
            )
        if snap.ram_pct > self.MAX_RAM_PCT:
            await self._notify_sir_throttled(
                "ram_high",
                f"Sir, RAM at {snap.ram_pct:.0f}% ({snap.ram_used_gb:.1f}/{snap.ram_total_gb:.1f}GB) — consider closing some applications."
            )
        if snap.disk_free_gb < self.MIN_DISK_FREE_GB:
            await self._notify_sir_throttled(
                "disk_low",
                f"Sir, only {snap.disk_free_gb:.1f}GB disk space remaining — please free up storage."
            )

    async def _notify_sir_throttled(self, alert_key: str, message: str):
        """
        Notify Sir with cooldown per alert type.
        NEW (2026-05-28): Same alert won't fire within ALERT_COOLDOWN_SECONDS.
        OLD: fired every check interval (every 60s = very annoying).
        """
        now = time.time()
        last = self._last_alert_time.get(alert_key, 0)
        if now - last < self.ALERT_COOLDOWN_SECONDS:
            logger.debug(f"Alert throttled ({alert_key}) — cooldown active")
            return
        self._last_alert_time[alert_key] = now
        await self._notify_sir(message)

    async def _log_size_loop(self):
        while self.running:
            await asyncio.sleep(self.LOG_CHECK_INTERVAL)
            await self._enforce_log_cap()

    async def _enforce_log_cap(self):
        log_dir = Path("./logs")
        if not log_dir.exists():
            return
        from datetime import date
        today_str = date.today().isoformat()
        total = sum(f.stat().st_size for f in log_dir.glob("*.log") if f.is_file())
        while total > self.LOG_CAP_BYTES:
            old_files = sorted(
                [f for f in log_dir.glob("manager_*.log") if today_str not in f.name],
                key=lambda f: f.name
            )
            if not old_files:
                break
            oldest = old_files[0]
            sz = oldest.stat().st_size
            oldest.unlink()
            total -= sz
            logger.info(f"Log rotation: deleted {oldest.name} ({sz/1024/1024:.1f}MB)")

    async def get_all_statuses(self) -> Dict[str, Dict]:
        return {
            name: {
                "healthy": s.healthy, "state": s.state,
                "fail_count": s.fail_count, "restart_count": s.restart_count,
                "last_error": s.last_error,
                "last_success": s.last_success.strftime("%H:%M:%S")
            }
            for name, s in self.statuses.items()
        }

    def get_hardware_summary(self) -> Dict:
        if not self.hardware_history:
            return {"available": False}
        snap = self.hardware_history[-1]
        return {
            "available": True,
            "cpu_pct": snap.cpu_pct, "cpu_temp": snap.cpu_temp,
            "ram_used_gb": snap.ram_used_gb, "ram_total_gb": snap.ram_total_gb,
            "ram_pct": snap.ram_pct,
            "gpu_pct": snap.gpu_pct, "gpu_vram_gb": snap.gpu_vram_used_gb,
            "disk_free_gb": snap.disk_free_gb,
            "network_recv_mbps": snap.network_recv_mbps,
        }

    def get_summary(self) -> str:
        total = len(self.statuses)
        healthy = sum(1 for s in self.statuses.values() if s.healthy)
        hw = self.get_hardware_summary()
        hw_str = ""
        if hw.get("available"):
            hw_str = f" | CPU {hw['cpu_pct']:.0f}% | RAM {hw['ram_pct']:.0f}%"
        if healthy == total:
            return f"All {total} agents operational{hw_str}, Sir."
        failed = [n for n, s in self.statuses.items() if not s.healthy]
        return f"{healthy}/{total} agents healthy. Issues: {', '.join(failed)}{hw_str}"

    async def get_status(self) -> Dict:
        return {"healthy": self.running, "state": "running" if self.running else "stopped"}

    async def _notify_sir(self, message: str):
        logger.critical(f"HEALTH ALERT: {message}")
        if self.notify_callback:
            try:
                await self.notify_callback(message)
            except Exception as e:
                logger.error(f"Notify failed: {e}")
        else:
            print(f"\n[MANAGER — HEALTH ALERT] {message}\n")

    async def stop(self):
        self.running = False
        for t in self._tasks:
            t.cancel()
        logger.info("Health agent stopped")
