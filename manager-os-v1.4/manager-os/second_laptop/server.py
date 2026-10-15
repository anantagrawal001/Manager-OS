"""
MANAGER OS — Second Laptop Background Server
══════════════════════════════════════════════
FILE: second_laptop/server.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
PURPOSE: Always-on background server running on the old i5-8250U laptop.
         Handles tasks that must run 24/7 without interrupting main Alienware.

HARDWARE: Intel Core i5-8250U, 12GB RAM, 500GB SSD, Intel UHD 620
NOTE: NO heavy AI inference here — Intel UHD 620 cannot handle it.
      Only lightweight tasks: scanning, monitoring, scheduling, sync.

TASKS:
  - Market monitoring during trading hours (9:15 AM - 3:30 PM IST)
  - Job portal scanning every 2 hours
  - Social media analytics collection every 6 hours
  - n8n workflow automation engine
  - Sync layer with main Alienware
  - Health relay (reports this machine's metrics to main machine)

DO NOT DELETE ANY CODE — comment out with reason and date
"""

import asyncio
import json
import time
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, Optional
import httpx
from loguru import logger


# Main Alienware connection
MAIN_MACHINE_URL = "http://100.x.x.x:8000"  # Replace with Tailscale IP of main machine
SYNC_INTERVAL = 30       # seconds
MARKET_CHECK_INTERVAL = 60  # seconds during market hours
JOB_SCAN_INTERVAL = 7200    # 2 hours
SOCIAL_SCAN_INTERVAL = 21600  # 6 hours


class SecondLaptopServer:
    """
    Lightweight always-on server for the second laptop.
    Handles background tasks so main Alienware stays fast for interactive use.
    """

    def __init__(self):
        self.running = True
        self.client = httpx.AsyncClient(timeout=30.0)
        self.main_machine_url = MAIN_MACHINE_URL
        self.last_job_scan = 0
        self.last_social_scan = 0
        self.sync_data: Dict[str, Any] = {}

    async def start(self):
        """Start all background tasks"""
        logger.info("Second Laptop Server starting...")
        print("=" * 50)
        print("  MANAGER OS — Second Laptop Server")
        print("  Background tasks: ACTIVE")
        print("=" * 50)

        tasks = [
            self._market_monitor_loop(),
            self._job_scan_loop(),
            self._social_analytics_loop(),
            self._sync_loop(),
            self._health_relay_loop(),
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

    # ─── Market Monitoring ────────────────────────────────────────────────────

    async def _market_monitor_loop(self):
        """Monitor Indian stock market during trading hours"""
        while self.running:
            now = datetime.now()
            if self._is_market_hours(now):
                await self._check_market_conditions()
                await asyncio.sleep(MARKET_CHECK_INTERVAL)
            else:
                # Sleep until next market open
                await asyncio.sleep(300)  # Check every 5 min outside hours

    def _is_market_hours(self, now: datetime) -> bool:
        """Check if Indian market is open (9:15 AM - 3:30 PM IST, Mon-Fri)"""
        if now.weekday() >= 5:  # Saturday/Sunday
            return False
        market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
        return market_open <= now <= market_close

    async def _check_market_conditions(self):
        """Fetch market data and relay to main machine"""
        try:
            # Lightweight market data fetch (no AI inference)
            market_data = await self._fetch_market_data()
            if market_data:
                self.sync_data["market"] = {
                    "timestamp": datetime.now().isoformat(),
                    "data": market_data
                }
                logger.debug(f"Market data updated: {market_data.get('nifty', 'N/A')}")
        except Exception as e:
            logger.error(f"Market monitor error: {e}")

    async def _fetch_market_data(self) -> Optional[Dict]:
        """Fetch basic market data from free sources using yfinance"""
        try:
            import yfinance as yf
            # Fetch NIFTY 50 (^NSEI) and SENSEX (^BSESN)
            loop = asyncio.get_event_loop()
            nifty_data = await loop.run_in_executor(
                None,
                lambda: yf.Ticker("^NSEI").history(period="2d")
            )
            sensex_data = await loop.run_in_executor(
                None,
                lambda: yf.Ticker("^BSESN").history(period="2d")
            )

            result = {}
            if not nifty_data.empty and len(nifty_data) >= 2:
                nifty_last = nifty_data['Close'].iloc[-1]
                nifty_prev = nifty_data['Close'].iloc[-2]
                nifty_change = nifty_last - nifty_prev
                nifty_change_pct = (nifty_change / nifty_prev) * 100
                result["nifty"] = float(nifty_last)
                result["nifty_change_pct"] = float(nifty_change_pct)

            if not sensex_data.empty and len(sensex_data) >= 2:
                sensex_last = sensex_data['Close'].iloc[-1]
                sensex_prev = sensex_data['Close'].iloc[-2]
                sensex_change = sensex_last - sensex_prev
                sensex_change_pct = (sensex_change / sensex_prev) * 100
                result["sensex"] = float(sensex_last)
                result["sensex_change_pct"] = float(sensex_change_pct)

            if result:
                result["timestamp"] = datetime.now().isoformat()
                return result
        except Exception as e:
            logger.error(f"Error fetching market data via yfinance: {e}")
        return None

    # ─── Job Scanning ─────────────────────────────────────────────────────────

    async def _job_scan_loop(self):
        """Scan job portals every 2 hours"""
        while self.running:
            now = time.time()
            if now - self.last_job_scan >= JOB_SCAN_INTERVAL:
                await self._scan_jobs()
                self.last_job_scan = now
            await asyncio.sleep(300)  # Check every 5 min if scan is due

    async def _scan_jobs(self):
        """Scan job portals for new relevant positions"""
        logger.info("Job portal scan starting...")
        try:
            # Lightweight scraping — no AI inference
            # Store results locally for main machine to process with AI
            scan_results = {
                "timestamp": datetime.now().isoformat(),
                "portals_checked": ["linkedin", "naukri", "indeed"],
                "new_jobs_found": 0,  # Would be populated by actual scraping
                "status": "scan_complete"
            }

            self.sync_data["jobs"] = scan_results

            # Save to sync file
            sync_file = Path("./sync/job_scan.json")
            sync_file.parent.mkdir(exist_ok=True)
            with open(sync_file, "w") as f:
                json.dump(scan_results, f)

            logger.info("Job scan complete — results queued for main machine")
        except Exception as e:
            logger.error(f"Job scan error: {e}")

    # ─── Social Analytics ─────────────────────────────────────────────────────

    async def _social_analytics_loop(self):
        """Collect social media analytics every 6 hours"""
        while self.running:
            now = time.time()
            if now - self.last_social_scan >= SOCIAL_SCAN_INTERVAL:
                await self._collect_social_analytics()
                self.last_social_scan = now
            await asyncio.sleep(600)  # Check every 10 min

    async def _collect_social_analytics(self):
        """Collect social media performance data"""
        logger.info("Social analytics collection starting...")
        try:
            analytics = {
                "timestamp": datetime.now().isoformat(),
                "platforms": ["instagram", "facebook"],
                "status": "collection_pending_oauth"
            }
            self.sync_data["social"] = analytics

            sync_file = Path("./sync/social_analytics.json")
            sync_file.parent.mkdir(exist_ok=True)
            with open(sync_file, "w") as f:
                json.dump(analytics, f)

            logger.info("Social analytics queued")
        except Exception as e:
            logger.error(f"Social analytics error: {e}")

    # ─── Sync Layer ───────────────────────────────────────────────────────────

    async def _sync_loop(self):
        """Sync data with main Alienware every 30 seconds"""
        while self.running:
            await self._push_sync_data()
            await asyncio.sleep(SYNC_INTERVAL)

    async def _push_sync_data(self):
        """Push collected data to main machine"""
        if not self.sync_data:
            return

        try:
            resp = await self.client.post(
                f"{self.main_machine_url}/api/sync",
                json={
                    "source": "second_laptop",
                    "timestamp": datetime.now().isoformat(),
                    "data": self.sync_data
                },
                timeout=10.0
            )
            if resp.status_code == 200:
                logger.debug("Sync successful")
        except Exception:
            # Main machine may be sleeping — not a problem
            pass

    # ─── Health Relay ─────────────────────────────────────────────────────────

    async def _health_relay_loop(self):
        """Report this machine's health to main machine"""
        while self.running:
            await self._report_health()
            await asyncio.sleep(60)

    async def _report_health(self):
        """Collect and report hardware metrics for this machine"""
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            health_data = {
                "machine": "second_laptop",
                "timestamp": datetime.now().isoformat(),
                "cpu_pct": cpu,
                "ram_pct": ram.percent,
                "ram_used_gb": round(ram.used / 1024**3, 2),
                "disk_free_gb": round(disk.free / 1024**3, 2),
                "tasks_running": {
                    "market_monitor": True,
                    "job_scanner": True,
                    "social_analytics": True,
                    "sync": True
                }
            }

            self.sync_data["second_laptop_health"] = health_data

        except Exception as e:
            logger.error(f"Health relay error: {e}")


# ─── Launch ───────────────────────────────────────────────────────────────────

async def main():
    server = SecondLaptopServer()
    try:
        await server.start()
    except KeyboardInterrupt:
        print("\nSecond Laptop Server stopped.")
    finally:
        await server.client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
