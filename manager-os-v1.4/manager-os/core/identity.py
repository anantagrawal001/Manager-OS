"""
MANAGER OS — Identity Guard
FILE: core/identity.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
UPDATED: 2026-05-31 | Phase B (P1-7)
CHANGE P1-7: verify_or_skip() non-blocking on boot — was blocking server start
             Hardware fingerprint captured on first run, verified on subsequent runs
             Passphrase stored as PBKDF2 hash in security/identity/
DO NOT DELETE — comment out with reason and date
"""

import asyncio
import hashlib
import hmac
import json
import os
import platform
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict

from loguru import logger

IDENTITY_DIR = Path("./security/identity")
FINGERPRINT_FILE = IDENTITY_DIR / "hardware.json"
PASSPHRASE_FILE = IDENTITY_DIR / "passphrase.hash"
ENROLLED_FLAG = IDENTITY_DIR / ".enrolled"


def _hash_passphrase(passphrase: str) -> str:
    salt = b"manager_os_phantom_anant_2024"
    return hashlib.pbkdf2_hmac("sha256", passphrase.encode(), salt, 100000).hex()


class IdentityGuard:
    def __init__(self, config: dict):
        self.config = config
        IDENTITY_DIR.mkdir(parents=True, exist_ok=True)
        self.enrolled = ENROLLED_FLAG.exists()
        self._fingerprint: Optional[Dict] = None

    @property
    def bypass_enabled(self) -> bool:
        return self.config.get("auth", {}).get("bypass_in_development", True)

    async def verify_or_skip(self) -> bool:
        """
        P1-7: Non-blocking boot verification.
        If bypass enabled → always grant access (dev mode).
        If enrolled → verify hardware fingerprint (fast, <1s).
        If not enrolled → allow boot, trigger enrollment in background.
        """
        if self.bypass_enabled:
            logger.debug("Identity: bypass_in_development=true — skipping verification")
            return True

        if not self.enrolled:
            logger.info("First run — enrollment will run in background")
            asyncio.create_task(self._background_enroll())
            return True

        return self._verify_hardware()

    def _verify_hardware(self) -> bool:
        """Fast hardware fingerprint check — <1 second."""
        if not FINGERPRINT_FILE.exists():
            return True  # No fingerprint stored yet

        try:
            stored = json.loads(FINGERPRINT_FILE.read_text())
            current = self._capture_fingerprint()
            # Check critical fields
            matches = sum(1 for k in ["hostname", "processor"]
                          if stored.get(k) == current.get(k))
            if matches >= 1:
                logger.info("Hardware verified — Manager OS access granted")
                return True
            else:
                logger.critical("Hardware fingerprint mismatch — unexpected machine")
                return False
        except Exception as e:
            logger.warning(f"Hardware fingerprint partial: {e}")
            return True  # Fail open on error — don't lock out Sir

    def _capture_fingerprint(self) -> Dict:
        """Capture hardware identifiers."""
        fp = {
            "hostname": platform.node(),
            "processor": platform.processor(),
            "system": platform.system(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "captured_at": datetime.now().isoformat(),
        }
        # Try Windows-specific identifiers
        if platform.system() == "Windows":
            try:
                r = subprocess.run(
                    ["wmic", "csproduct", "get", "uuid"],
                    capture_output=True, text=True, timeout=5
                )
                if r.returncode == 0:
                    lines = [l.strip() for l in r.stdout.strip().split("\n") if l.strip() and l.strip() != "UUID"]
                    if lines:
                        fp["system_uuid"] = lines[0]
            except Exception as e:
                logger.warning(f"Hardware fingerprint partial: {e}")
        return fp

    # Superseded 2026-10-12: retained for rollback; corrected implementation below.
    # async def enroll(self) -> bool:
    #     """Full enrollment — called on first run via SETUP.bat."""
    #     logger.info("=== MANAGER OS — FIRST RUN ENROLLMENT ===")
    #
    #     IDENTITY_DIR.mkdir(parents=True, exist_ok=True)
    #
    #     # Capture + save hardware fingerprint
    #     fp = self._capture_fingerprint()
    #     FINGERPRINT_FILE.write_text(json.dumps(fp, indent=2))
    #     logger.info("Hardware fingerprint captured and saved")
    #
    #     # Passphrase enrollment
    #     print("\n[Manager] Please set a backup passphrase (used if voice fails):")
    #     if os.environ.get("SETUP_UNATTENDED") == "1":
    #         default = "hey manager lets buckle up"
    #         PASSPHRASE_FILE.write_text(_hash_passphrase(default))
    #         logger.info("Using default passphrase (unattended mode)")
    #     else:
    #         try:
    #             passphrase = input("Passphrase: ").strip()
    #             if passphrase:
    #                 PASSPHRASE_FILE.write_text(_hash_passphrase(passphrase))
    #                 logger.info("Passphrase enrolled")
    #             else:
    #                 # Use default passphrase
    #                 default = "hey manager lets buckle up"
    #                 PASSPHRASE_FILE.write_text(_hash_passphrase(default))
    #                 logger.info("Using default passphrase")
    #         except (EOFError, KeyboardInterrupt):
    #             default = "hey manager lets buckle up"
    #             PASSPHRASE_FILE.write_text(_hash_passphrase(default))
    #
    #     ENROLLED_FLAG.touch()
    #     self.enrolled = True
    #     logger.info("Enrollment complete — Manager OS is now locked to Sir")
    #     return True

    async def enroll(self):
        from security.auth import load_passphrase_hash, enroll_passphrase
        if load_passphrase_hash():
            self.enrolled = True
            return True
        if os.environ.get('SETUP_UNATTENDED') == '1':
            logger.info('Create a passphrase in the dashboard on first use')
            return False
        import getpass
        try:
            passphrase = await asyncio.to_thread(getpass.getpass, 'Create passphrase (8+ characters): ')
            enroll_passphrase(passphrase)
        except (ValueError, EOFError, KeyboardInterrupt):
            return False
        self.enrolled = True
        return True

    # Superseded 2026-10-12: retained for rollback; corrected implementation below.
    # async def _background_enroll(self):
    #     """Run enrollment silently after server starts — P1-7."""
    #     await asyncio.sleep(5)
    #     try:
    #         fp = self._capture_fingerprint()
    #         FINGERPRINT_FILE.write_text(json.dumps(fp, indent=2))
    #         default_pass = self.config.get("identity", {}).get("default_passphrase",
    #                                                             "hey manager lets buckle up")
    #         PASSPHRASE_FILE.write_text(_hash_passphrase(default_pass))
    #         ENROLLED_FLAG.touch()
    #         self.enrolled = True
    #         logger.info("Background enrollment complete")
    #     except Exception as e:
    #         logger.error(f"Background enrollment error: {e}")

    async def _background_enroll(self):
        logger.info('Identity enrollment is available in the dashboard. No default passphrase is created.')

    # Superseded 2026-10-12: retained for rollback; corrected implementation below.
    # def verify_passphrase(self, passphrase: str) -> bool:
    #     if not PASSPHRASE_FILE.exists():
    #         return bool(passphrase)
    #     stored = PASSPHRASE_FILE.read_text().strip()
    #     return hmac.compare_digest(_hash_passphrase(passphrase), stored)

    def verify_passphrase(self, passphrase):
        from security.auth import verify_passphrase
        return verify_passphrase(passphrase)
