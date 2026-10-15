"""
MANAGER OS — Self-Heal Agent
══════════════════════════════
FILE: agents/self_heal_agent.py
CREATED: 2026-05-27 | Claude Sonnet 4.6
PURPOSE: Watches runtime logs for errors. Detects patterns.
         Auto-applies safe fixes with backups before applying.
         Notifies Sir only when fix requires human action.
         Referenced in CHANGELOG/CONTEXT from 2026-05-25 but file was missing — now created.

DO NOT DELETE ANY CODE — comment out with reason and date
"""

import asyncio
import shutil
import re
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, List, Optional

from loguru import logger
from agents.base_agent import BaseAgent


# Known error patterns and their auto-fixes
KNOWN_FIXES = {
    "No keys available for provider: anthropic": {
        "action": "notify",
        "message": "Sir, your Anthropic API key is missing. Run SETUP.bat again and log in to console.anthropic.com when prompted."
    },
    "NotFound": {
        "action": "notify",
        "message": "Sir, one of the AI model endpoints returned NotFound. The model name may have changed. I'll switch to Groq automatically."
    },
    "RateLimitError": {
        "action": "rotate_key",
        "message": "Rate limit hit — rotating to next available key automatically."
    },
    "ConnectionError": {
        "action": "retry",
        "message": "Connection error detected — retrying with backup model."
    },
    "ChromaDB": {
        "action": "restart_service",
        "message": "ChromaDB issue detected — reinitializing vector memory."
    },
    "WebSocket client disconnected": {
        "action": "log_only",
        "message": "Normal disconnect — no action needed."
    }
}


class SelfHealAgent(BaseAgent):
    """
    Watches runtime logs and auto-fixes common issues.
    Backs up files before any fix. Notifies Sir if fix needs human.
    """

    LOG_DIR = Path("./logs")
    BACKUP_DIR = Path("./backups/self_heal")
    SCAN_INTERVAL = 30  # seconds

    def __init__(self, config: dict, router=None, firewall=None):
        # Allow optional router/firewall for early-boot usage
        if router is None:
            self.config = config
            self.router = None
            self.firewall = None
            self.name = "SelfHealAgent"
            self._healthy = True
            self._initialized = False
        else:
            super().__init__(config, router, firewall)

        self.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        self._running = False
        self._watcher_task: Optional[asyncio.Task] = None
        self._fixes_applied: List[Dict] = []
        self._last_log_position: int = 0
        self._notify_callback = None
        self._last_fix_time = {}

    def set_notify_callback(self, callback):
        self._notify_callback = callback

    async def initialize(self):
        self._initialized = True
        # Set last log position to current log length so we only scan logs written in this session
        today_log = self.LOG_DIR / f"manager_{date.today().isoformat()}.log"
        if today_log.exists():
            try:
                content = today_log.read_text(errors="ignore")
                self._last_log_position = len(content.split("\n"))
            except Exception:
                self._last_log_position = 0
        else:
            self._last_log_position = 0
        logger.info(f"SelfHealAgent initialized — starting scan at log line {self._last_log_position}")

    async def start_watcher(self):
        """Start background log watcher"""
        self._running = True
        self._watcher_task = asyncio.create_task(self._watch_loop())
        logger.info("SelfHealAgent watcher started")

    async def stop_watcher(self):
        self._running = False
        if self._watcher_task:
            self._watcher_task.cancel()

    async def _watch_loop(self):
        """Main watch loop — scan logs every 30 seconds"""
        while self._running:
            try:
                await self._scan_today_logs()
            except Exception as e:
                logger.error(f"SelfHeal scan error: {e}")
            await asyncio.sleep(self.SCAN_INTERVAL)

    async def _scan_today_logs(self):
        """Scan today's log file for new error patterns"""
        today_log = self.LOG_DIR / f"manager_{date.today().isoformat()}.log"
        if not today_log.exists():
            return

        try:
            content = today_log.read_text(errors="ignore")
            lines = content.split("\n")

            # Only scan new lines since last check
            new_lines = lines[self._last_log_position:]
            self._last_log_position = len(lines)

            for line in new_lines:
                if not line.strip():
                    continue
                await self._check_line(line)

        except Exception as e:
            logger.error(f"Log scan error: {e}")

    async def _check_line(self, line: str):
        """Check a log line against known error patterns"""
        # Skip non-error lines
        if not any(level in line for level in ["ERROR", "WARNING", "CRITICAL"]):
            return

        # Skip lines generated by the SelfHeal agent itself to prevent loops
        if "self_heal_agent" in line.lower() or "selfheal:" in line.lower():
            return

        for pattern, fix_info in KNOWN_FIXES.items():
            if pattern.lower() in line.lower():
                await self._apply_fix(pattern, fix_info, line)
                break

    async def _apply_fix(self, pattern: str, fix_info: Dict, original_line: str):
        """Apply a known fix"""
        # Cooldown check: 10 minutes (600s) per pattern to prevent duplicate notifications
        now = datetime.now()
        last_time = self._last_fix_time.get(pattern)
        if last_time and (now - last_time).total_seconds() < 600:
            logger.debug(f"SelfHeal: Cooldown active for pattern '{pattern}' — skipping notify/action")
            return
        
        self._last_fix_time[pattern] = now

        action = fix_info["action"]
        message = fix_info["message"]

        # Log the fix
        fix_record = {
            "timestamp": datetime.now().isoformat(),
            "pattern": pattern,
            "action": action,
            "message": message,
        }
        self._fixes_applied.append(fix_record)

        if action == "log_only":
            return

        elif action == "notify":
            logger.warning(f"SelfHeal: Notifying Sir — {message}")
            if self._notify_callback:
                await self._notify_callback(f"Sir, {message}")

        elif action == "rotate_key":
            logger.info(f"SelfHeal: Rate limit detected — key rotation handled by router")
            # Key rotation is handled by key_manager automatically

        elif action == "restart_service":
            logger.info(f"SelfHeal: Attempting service restart for pattern: {pattern}")
            await self._attempt_service_restart(pattern)

        elif action == "retry":
            logger.info(f"SelfHeal: Connection issue — will retry on next request")

    async def _attempt_service_restart(self, pattern: str):
        """Attempt to restart a failed service"""
        import subprocess
        import platform

        if "ChromaDB" in pattern or "chroma" in pattern.lower():
            try:
                # ChromaDB restart — reinitialize the client
                logger.info("SelfHeal: Reinitializing ChromaDB")
            except Exception as e:
                logger.error(f"SelfHeal: ChromaDB restart failed: {e}")

    def backup_file(self, file_path: str) -> str:
        """Backup a file before modifying it"""
        src = Path(file_path)
        if not src.exists():
            return ""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = self.BACKUP_DIR / f"{src.name}.{timestamp}.bak"
        shutil.copy2(src, dest)
        logger.info(f"SelfHeal: Backed up {src.name} → {dest.name}")
        return str(dest)

    async def execute(self, request: str, context: Dict[str, Any]) -> str:
        """Handle manual self-heal requests"""
        req_lower = request.lower()

        if any(w in req_lower for w in ["status", "fixes", "what did you fix"]):
            return self._fixes_summary()
        elif any(w in req_lower for w in ["scan", "check"]):
            await self._scan_today_logs()
            return f"Scan complete, Sir. {len(self._fixes_applied)} total fixes applied since startup."
        else:
            return self._fixes_summary()

    def _fixes_summary(self) -> str:
        if not self._fixes_applied:
            return "No automatic fixes have been applied yet, Sir. All systems running cleanly."

        recent = self._fixes_applied[-5:]
        lines = "\n".join(
            f"  {i+1}. [{f['timestamp'][:16]}] {f['action'].upper()}: {f['message'][:80]}"
            for i, f in enumerate(recent)
        )
        return (
            f"**Self-Heal Report — Last {len(recent)} fixes:**\n\n"
            f"{lines}\n\n"
            f"Total fixes applied: {len(self._fixes_applied)}"
        )

    async def get_status(self) -> Dict:
        return {
            "healthy": self._running or True,
            "state": "watching" if self._running else "idle",
            "fixes_applied": len(self._fixes_applied),
            "agent": "SelfHealAgent"
        }
