"""
MANAGER OS — Key Manager
═════════════════════════
FILE: core/key_manager.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
UPDATED: 2026-05-28 | Claude Sonnet 4.6
CHANGE: Uses unified provider_names.py registry — fixes name mismatch that caused
        all cloud models to fail. Vault stores canonical names only.

DO NOT DELETE ANY CODE — comment out with reason and date
"""

import json
import time
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from cryptography.fernet import Fernet
from loguru import logger

from core.provider_names import CLOUD_PROVIDERS, display, OLLAMA


@dataclass
class APIKey:
    provider: str
    key: str
    account_label: str
    daily_limit_requests: int = 1000
    daily_limit_tokens: int = 100000
    requests_today: int = 0
    tokens_today: int = 0
    last_reset: str = field(default_factory=lambda: date.today().isoformat())
    blocked_until: Optional[float] = None
    is_active: bool = True

    @property
    def usage_pct(self) -> float:
        r = self.requests_today / max(self.daily_limit_requests, 1)
        t = self.tokens_today / max(self.daily_limit_tokens, 1)
        return max(r, t)

    @property
    def is_blocked(self) -> bool:
        return bool(self.blocked_until and time.time() < self.blocked_until)

    def reset_if_new_day(self):
        today = date.today().isoformat()
        if self.last_reset != today:
            self.requests_today = 0
            self.tokens_today = 0
            self.last_reset = today
            self.blocked_until = None


PROVIDER_LIMITS = {
    "anthropic":   {"requests": 1000,  "tokens": 100000},
    "google":      {"requests": 15000, "tokens": 1000000},
    "openai":      {"requests": 200,   "tokens": 40000},
    "groq":        {"requests": 14400, "tokens": 500000},
    "nvidia":      {"requests": 1000,  "tokens": 100000},
    "elevenlabs":  {"requests": 10000, "tokens": 10000},
    "huggingface": {"requests": 10000, "tokens": 500000},
    "deepseek":    {"requests": 5000,  "tokens": 200000},
    "stability":   {"requests": 500,   "tokens": 500},
}

ROTATION_THRESHOLD = 0.80
VAULT_PATH = Path("./security/key_vault.enc")
KEY_FILE = Path("./security/identity/.key")


class KeyManager:
    def __init__(self, config: dict):
        self.config = config
        self.pools: Dict[str, List[APIKey]] = {}
        self.current_index: Dict[str, int] = {}
        self._fernet: Optional[Fernet] = None
        self._setup_encryption()
        self._load_vault()

    def _setup_encryption(self):
        KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
        if KEY_FILE.exists():
            with open(KEY_FILE, "rb") as f:
                key = f.read()
            try:
                self._fernet = Fernet(key)
            except Exception:
                self._fernet = None
        else:
            key = Fernet.generate_key()
            with open(KEY_FILE, "wb") as f:
                f.write(key)
            self._fernet = Fernet(key)

    def _load_vault(self):
        if not VAULT_PATH.exists():
            logger.info("No key vault found — loading from config")
            self._load_from_config()
            return

        try:
            with open(VAULT_PATH, "rb") as f:
                raw = f.read()

            if self._fernet:
                try:
                    data = json.loads(self._fernet.decrypt(raw))
                except Exception:
                    # Try plain JSON fallback
                    try:
                        data = json.loads(raw)
                    except Exception:
                        logger.warning("Vault unreadable — loading from config")
                        self._load_from_config()
                        return
            else:
                data = json.loads(raw)

            for provider, keys_data in data.items():
                limits = PROVIDER_LIMITS.get(provider, {"requests": 1000, "tokens": 100000})
                self.pools[provider] = []
                for kd in keys_data:
                    api_key = APIKey(
                        provider=provider,
                        key=kd["key"],
                        account_label=kd.get("label", "account_1"),
                        daily_limit_requests=limits["requests"],
                        daily_limit_tokens=limits["tokens"],
                        requests_today=kd.get("requests_today", 0),
                        tokens_today=kd.get("tokens_today", 0),
                        last_reset=kd.get("last_reset", date.today().isoformat()),
                    )
                    api_key.reset_if_new_day()
                    self.pools[provider].append(api_key)
                self.current_index[provider] = max(0, len(self.pools[provider]) - 1)
                logger.info(f"Loaded {len(self.pools[provider])} key(s) for {display(provider)}")

        except Exception as e:
            logger.error(f"Vault load error: {e} — loading from config")
            self._load_from_config()

    def _load_from_config(self):
        """Load keys from config.yaml — using canonical provider names"""
        api_keys = self.config.get("api_keys", {})
        # OLD (2026-05-24): used "google_ai" — caused mismatch with router
        # NEW (2026-05-28): use canonical names from provider_names.py
        # Config may still have old keys like "google_ai" — map them
        old_to_canonical = {
            "google_ai":    "google",
            "stability_ai": "stability",
        }
        for old_name, canonical in old_to_canonical.items():
            if old_name in api_keys and canonical not in api_keys:
                api_keys[canonical] = api_keys[old_name]

        for provider in CLOUD_PROVIDERS:
            key_value = api_keys.get(provider)
            if key_value:
                self.add_key(provider, key_value, "config_key")

    def _save_vault(self):
        VAULT_PATH.parent.mkdir(parents=True, exist_ok=True)
        vault_data = {
            provider: [
                {"key": k.key, "label": k.account_label,
                 "requests_today": k.requests_today,
                 "tokens_today": k.tokens_today,
                 "last_reset": k.last_reset}
                for k in keys
            ]
            for provider, keys in self.pools.items()
        }
        data_bytes = json.dumps(vault_data).encode()
        if self._fernet:
            data_bytes = self._fernet.encrypt(data_bytes)
        with open(VAULT_PATH, "wb") as f:
            f.write(data_bytes)

    def add_key(self, provider: str, key: str, label: str = "account_1"):
        if provider not in self.pools:
            self.pools[provider] = []
            self.current_index[provider] = 0
        existing = [k.key for k in self.pools[provider]]
        if key in existing:
            return
        limits = PROVIDER_LIMITS.get(provider, {"requests": 1000, "tokens": 100000})
        self.pools[provider].append(APIKey(
            provider=provider, key=key, account_label=label,
            daily_limit_requests=limits["requests"],
            daily_limit_tokens=limits["tokens"],
        ))
        self.current_index[provider] = len(self.pools[provider]) - 1
        self._save_vault()
        logger.info(f"Key added for {display(provider)} (pool: {len(self.pools[provider])})")

    def get_key(self, provider: str) -> Optional[str]:
        if provider == OLLAMA:
            return "local"  # No key needed
        pool = self.pools.get(provider, [])
        if not pool:
            return None
        start = self.current_index.get(provider, 0)
        for offset in range(len(pool)):
            idx = (start + offset) % len(pool)
            k = pool[idx]
            k.reset_if_new_day()
            if k.is_blocked or not k.is_active:
                continue
            if k.usage_pct >= ROTATION_THRESHOLD:
                continue
            self.current_index[provider] = idx
            return k.key
        # All above threshold — use least loaded
        available = [k for k in pool if not k.is_blocked and k.is_active]
        if available:
            least = min(available, key=lambda k: k.usage_pct)
            if least.usage_pct < 1.0:
                return least.key
        return None

    def record_usage(self, provider: str, requests: int = 1, tokens: int = 0):
        idx = self.current_index.get(provider, 0)
        pool = self.pools.get(provider, [])
        if pool and idx < len(pool):
            pool[idx].requests_today += requests
            pool[idx].tokens_today += tokens
            if pool[idx].requests_today % 10 == 0:
                self._save_vault()

    def get_all_keys_for_config(self) -> Dict[str, str]:
        """Get best key per provider for injecting into config"""
        result = {}
        for provider in self.pools:
            key = self.get_key(provider)
            if key and key != "local":
                result[provider] = key
        return result

    def get_pool_status(self) -> Dict:
        return {
            provider: {
                "total": len(pool),
                "available": sum(1 for k in pool if not k.is_blocked and k.usage_pct < 1.0),
                "usage": f"{pool[0].usage_pct:.0%}" if pool else "0%",
            }
            for provider, pool in self.pools.items()
        }
