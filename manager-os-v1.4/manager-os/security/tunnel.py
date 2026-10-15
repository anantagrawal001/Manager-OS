"""
MANAGER OS — Tailscale Private Network
════════════════════════════════════════
FILE: security/tunnel.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
PURPOSE: Private network tunnel via Tailscale.
         Anant can access Manager OS from anywhere in the world.
         Dashboard never exposed to public internet.
         setup.bat installs Tailscale silently — Anant logs in once, done forever.

WHY TAILSCALE (not WireGuard):
  WireGuard requires: port forwarding, network config knowledge
  Tailscale requires: one install, one login — works everywhere automatically
  See ARCH.md ADR-011-UPDATED

DO NOT DELETE ANY CODE — comment out with reason and date
"""

import subprocess
import platform
import asyncio
from pathlib import Path
from typing import Optional
from loguru import logger


class TailscaleManager:
    """
    Manages Tailscale private network for remote Manager OS access.
    """

    TAILSCALE_INSTALLER_URL = "https://pkgs.tailscale.com/stable/tailscale-setup.exe"

    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get("vpn", {}).get("enabled", False)
        self._tailscale_ip: Optional[str] = None

    async def setup(self) -> bool:
        """
        Full Tailscale setup — called from setup.bat.
        1. Check if installed
        2. If not → download and install silently
        3. Check if authenticated
        4. If not → open auth URL for Anant to log in
        5. Get Tailscale IP for dashboard access
        """
        if not self._is_installed():
            logger.info("Tailscale not found — installing...")
            success = await self._install()
            if not success:
                logger.error("Tailscale installation failed")
                return False

        if not self._is_authenticated():
            logger.info("Tailscale not authenticated — opening login...")
            await self._open_login()
            # Wait for authentication
            for _ in range(60):  # Wait up to 5 minutes
                await asyncio.sleep(5)
                if self._is_authenticated():
                    break
            else:
                logger.warning("Tailscale authentication timed out")
                return False

        # Get Tailscale IP
        self._tailscale_ip = self._get_tailscale_ip()
        if self._tailscale_ip:
            logger.info(f"Tailscale active — Manager OS accessible at: {self._tailscale_ip}:8000")
            return True

        return False

    def _is_installed(self) -> bool:
        """Check if Tailscale is installed"""
        try:
            result = subprocess.run(["tailscale", "version"], capture_output=True, timeout=5)
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _is_authenticated(self) -> bool:
        """Check if Tailscale is authenticated and connected"""
        try:
            result = subprocess.run(
                ["tailscale", "status", "--json"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                import json
                status = json.loads(result.stdout)
                return status.get("BackendState") == "Running"
        except Exception:
            pass
        return False

    def _get_tailscale_ip(self) -> Optional[str]:
        """Get this machine's Tailscale IP address"""
        try:
            result = subprocess.run(
                ["tailscale", "ip", "-4"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return None

    async def _install(self) -> bool:
        """Install Tailscale silently"""
        try:
            if platform.system() == "Windows":
                # Download installer
                import urllib.request
                installer_path = Path("./setup/tailscale-setup.exe")
                installer_path.parent.mkdir(exist_ok=True)
                urllib.request.urlretrieve(self.TAILSCALE_INSTALLER_URL, installer_path)

                # Silent install
                result = subprocess.run(
                    [str(installer_path), "/install", "/quiet"],
                    timeout=120
                )
                return result.returncode == 0
        except Exception as e:
            logger.error(f"Tailscale install error: {e}")
        return False

    async def _open_login(self):
        """Open Tailscale login in browser"""
        try:
            subprocess.Popen(["tailscale", "up"])
            logger.info("Tailscale login page opened — Sir, please log in with your Tailscale account")
            print("\n[Manager] Sir, please log in to Tailscale in the browser window that just opened.")
            print("[Manager] Once logged in, press Enter to continue.\n")
        except Exception as e:
            logger.error(f"Failed to open Tailscale login: {e}")

    def get_dashboard_url(self) -> str:
        """Get the remote dashboard URL"""
        if self._tailscale_ip:
            return f"http://{self._tailscale_ip}:8000"
        return "http://localhost:8000 (Tailscale not active — local access only)"

    def get_status(self) -> dict:
        return {
            "enabled": self.enabled,
            "installed": self._is_installed(),
            "authenticated": self._is_authenticated(),
            "tailscale_ip": self._tailscale_ip,
            "dashboard_url": self.get_dashboard_url()
        }
