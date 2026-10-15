"""
MANAGER OS — Log Manager
═════════════════════════
FILE: core/log_manager.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
PURPOSE: Rolling log system. Daily log files. 5GB total cap.
         When total exceeds 5GB → oldest day deleted → newest day written.
         Continuous cycle. Logs never fill storage. Never lose current day.

LOG TYPES: system, api-calls, trades, errors, health, agent-activity, conversations

DO NOT DELETE ANY CODE — comment out with reason and date
"""

import json
import os
import shutil
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional
import asyncio

from loguru import logger


LOG_DIR = Path("./logs")
MAX_TOTAL_SIZE_BYTES = 5 * 1024 * 1024 * 1024  # 5GB
TARGET_DAILY_SIZE_BYTES = 100 * 1024 * 1024      # 100MB per day (guideline)


class LogManager:
    """
    Rolling log manager.
    
    Structure:
        logs/
            manager_2026-05-24.log     ← today
            manager_2026-05-23.log     ← yesterday
            manager_2026-05-22.log     ← day before
            ...
            (oldest deleted when total > 5GB)
    
    Rotation rule:
        - Total size > 5GB → delete oldest dated file
        - Repeat until under 5GB
        - Never delete today's file
    """

    def __init__(self):
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.today_log = LOG_DIR / f"manager_{date.today().isoformat()}.log"
        self._setup_loguru()
        self._schedule_rotation()

    def _setup_loguru(self):
        """Configure loguru to write to today's dated log file"""
        # Remove default loguru sink
        logger.remove()

        # Console sink — INFO and above
        logger.add(
            sink=lambda msg: print(msg, end=""),
            level="INFO",
            colorize=True,
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}"
        )

        # Today's log file — all levels
        logger.add(
            sink=str(self.today_log),
            level="DEBUG",
            rotation="00:00",          # New file at midnight
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}",
            encoding="utf-8",
            serialize=False,
            retention=None,            # We handle retention ourselves
            compression=None,
        )

        logger.info(f"Log manager initialized — writing to {self.today_log}")

    def _schedule_rotation(self):
        """Schedule daily rotation check"""
        self._rotation_task = asyncio.create_task(self._rotation_loop()) if asyncio.get_event_loop().is_running() else None

    async def _rotation_loop(self):
        """Run rotation check every hour"""
        while True:
            await asyncio.sleep(3600)  # Every hour
            self._enforce_size_cap()
            self._update_today_log()

    def _update_today_log(self):
        """Update reference to today's log file (handles midnight rollover)"""
        new_today = LOG_DIR / f"manager_{date.today().isoformat()}.log"
        if new_today != self.today_log:
            self.today_log = new_today
            logger.info(f"New log day: {self.today_log}")

    def _enforce_size_cap(self):
        """
        Enforce 5GB total cap.
        Delete oldest log files until total is under cap.
        Never delete today's file.
        """
        today_str = date.today().isoformat()

        while True:
            total_size = self._get_total_log_size()

            if total_size <= MAX_TOTAL_SIZE_BYTES:
                break

            # Find oldest log file (excluding today)
            log_files = sorted(
                [f for f in LOG_DIR.glob("manager_*.log") if today_str not in f.name],
                key=lambda f: f.name
            )

            if not log_files:
                logger.warning("All old logs deleted but still over 5GB — today's log is large")
                break

            oldest = log_files[0]
            size_mb = oldest.stat().st_size / (1024 * 1024)
            logger.info(f"Log cap enforced: deleting {oldest.name} ({size_mb:.1f}MB)")
            oldest.unlink()

    def _get_total_log_size(self) -> int:
        """Get total size of all log files in bytes"""
        return sum(f.stat().st_size for f in LOG_DIR.glob("*.log") if f.is_file())

    def get_log_stats(self) -> dict:
        """Get current log statistics"""
        all_logs = sorted(LOG_DIR.glob("manager_*.log"))
        total_size = self._get_total_log_size()

        return {
            "total_files": len(all_logs),
            "total_size_gb": round(total_size / (1024**3), 3),
            "cap_gb": 5.0,
            "cap_used_pct": round(total_size / MAX_TOTAL_SIZE_BYTES * 100, 1),
            "oldest_log": all_logs[0].name if all_logs else None,
            "newest_log": all_logs[-1].name if all_logs else None,
            "today_log_size_mb": round(self.today_log.stat().st_size / (1024**2), 2) if self.today_log.exists() else 0,
        }

    # ─── Structured log writers ───────────────────────────────────────────────

    def log_api_call(self, provider: str, model: str, tokens_used: int, latency_ms: int,
                     success: bool, task_type: str = ""):
        """Log every API call with metrics"""
        logger.bind(log_type="api").info(
            f"API | {provider}/{model} | {task_type} | "
            f"tokens={tokens_used} | latency={latency_ms}ms | success={success}"
        )

    def log_trade(self, ticker: str, action: str, confidence: float,
                  approved: bool, reason: str, mode: str = "paper"):
        """Log every trade signal and decision"""
        logger.bind(log_type="trade").info(
            f"TRADE | {mode.upper()} | {ticker} | {action} | "
            f"confidence={confidence:.0%} | approved={approved} | {reason}"
        )

    def log_health_check(self, component: str, healthy: bool, metric: str = "", value: str = ""):
        """Log health check results"""
        level = "DEBUG" if healthy else "WARNING"
        logger.bind(log_type="health").log(
            level,
            f"HEALTH | {component} | {'OK' if healthy else 'ISSUE'} | {metric}={value}"
        )

    def log_hardware(self, cpu_pct: float, ram_used_gb: float, ram_total_gb: float,
                     gpu_pct: float, disk_free_gb: float):
        """Log hardware metrics"""
        logger.bind(log_type="hardware").debug(
            f"HW | CPU={cpu_pct:.1f}% | RAM={ram_used_gb:.1f}/{ram_total_gb:.1f}GB | "
            f"GPU={gpu_pct:.1f}% | Disk_free={disk_free_gb:.1f}GB"
        )

    def log_agent_activity(self, agent: str, action: str, duration_ms: int, success: bool):
        """Log agent actions"""
        logger.bind(log_type="agent").info(
            f"AGENT | {agent} | {action} | {duration_ms}ms | {'OK' if success else 'FAILED'}"
        )

    def log_key_rotation(self, provider: str, from_key: str, to_key: str, reason: str):
        """Log API key rotations"""
        logger.bind(log_type="security").info(
            f"KEY_ROTATION | {provider} | {from_key} → {to_key} | {reason}"
        )
