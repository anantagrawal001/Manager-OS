"""
MANAGER OS — Authentication
FILE: security/auth.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
UPDATED: 2026-05-31 | Claude Sonnet 4.6 — PHASE A (P0-2, P0-4)
CHANGES:
  P0-2: Real server-side session token. /api/auth validates passphrase against stored hash.
        Token stored in memory. All protected endpoints check token via require_auth().
        bypass_in_development: true in config skips verification for dev convenience.
  P0-4: /api/key/add now requires auth token. Rate limited (5 req/min).
DO NOT DELETE ANY CODE — comment out with reason and date
"""

import hashlib
import hmac
import os
import secrets
import time
from functools import wraps
from pathlib import Path
from typing import Optional, Dict

from fastapi import Request, HTTPException
from loguru import logger


# In-memory session store (single user, so one active session is fine)
_sessions: Dict[str, float] = {}  # token -> expiry timestamp
SESSION_TTL = 8 * 3600  # 8 hours
PASSPHRASE_FILE = Path("./security/identity/passphrase.hash")
_rate_limits: Dict[str, list] = {}  # endpoint -> [timestamps]


def _hash_passphrase(passphrase: str) -> str:
    salt = b"manager_os_phantom_anant_2024"
    return hashlib.pbkdf2_hmac("sha256", passphrase.encode(), salt, 100000).hex()


def load_passphrase_hash() -> Optional[str]:
    if PASSPHRASE_FILE.exists():
        return PASSPHRASE_FILE.read_text().strip()
    return None


# Superseded 2026-10-12: retained for rollback; corrected implementation below.
# def verify_passphrase(passphrase: str) -> bool:
#     """Verify passphrase against stored hash. True if bypass enabled or hash matches."""
#     stored = load_passphrase_hash()
#     if not stored:
#         # No passphrase enrolled yet — allow any non-empty passphrase
#         return bool(passphrase and passphrase.strip())
#     return hmac.compare_digest(_hash_passphrase(passphrase), stored)

def verify_passphrase(passphrase):
    stored = load_passphrase_hash()
    if not stored or not isinstance(passphrase, str):
        return False
    if stored.startswith('v2$'):
        _, salt, expected = stored.split('$')
        actual = hashlib.pbkdf2_hmac('sha256', passphrase.encode(), bytes.fromhex(salt), 600000).hex()
        return hmac.compare_digest(actual, expected)
    return hmac.compare_digest(_hash_passphrase(passphrase), stored)


def enroll_passphrase(passphrase):
    if len(passphrase) < 8:
        raise ValueError('Use at least 8 characters for your passphrase')
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', passphrase.encode(), salt, 600000).hex()
    PASSPHRASE_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with PASSPHRASE_FILE.open('x', encoding='utf-8') as f:
            f.write(f'v2${salt.hex()}${digest}')
    except FileExistsError:
        raise ValueError('Already enrolled. Sign in with your existing passphrase.')


def create_session() -> str:
    token = secrets.token_hex(32)
    _sessions[token] = time.time() + SESSION_TTL
    # Clean expired sessions
    expired = [t for t, exp in _sessions.items() if time.time() > exp]
    for t in expired:
        del _sessions[t]
    logger.info(f"Session created — expires in 8h")
    return token


def validate_token(token: str) -> bool:
    if not token or token not in _sessions:
        return False
    if time.time() > _sessions[token]:
        del _sessions[token]
        return False
    return True


def revoke_session(token):
    _sessions.pop(token, None)


def get_token_from_request(request: Request) -> Optional[str]:
    """Extract token from Authorization header or query param."""
    # Check Authorization: Bearer <token>
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    # Check query param ?token=...
    return request.query_params.get("token")


def require_auth(request: Request, bypass_in_dev: bool = False) -> str:
    """Dependency — raises 401 if not authenticated. Returns token if valid."""
    if bypass_in_dev:
        return "dev_bypass"
    token = get_token_from_request(request)
    if not token or not validate_token(token):
        raise HTTPException(status_code=401, detail="Authentication required")
    return token


def check_rate_limit(key: str, max_per_minute: int = 5) -> bool:
    """Simple rate limiter. Returns True if within limit."""
    now = time.time()
    if key not in _rate_limits:
        _rate_limits[key] = []
    # Keep only last minute
    _rate_limits[key] = [t for t in _rate_limits[key] if now - t < 60]
    if len(_rate_limits[key]) >= max_per_minute:
        return False
    _rate_limits[key].append(now)
    return True
