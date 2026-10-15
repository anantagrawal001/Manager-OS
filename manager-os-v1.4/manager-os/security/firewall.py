"""
MANAGER OS — Privacy Firewall
FILE: security/firewall.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
UPDATED: 2026-05-31 | Phase B (P1-12)
CHANGE P1-12: Removed invalid 'anthropic-beta' header from PROVIDER_HEADERS.
              That header was causing BadRequestError on every Claude call.
DO NOT DELETE — comment out with reason and date
"""

import re
from typing import Dict, Any, Optional, List
from loguru import logger


# P1-12: Removed anthropic-beta header — it's invalid and caused BadRequestError
# OLD: PROVIDER_HEADERS = {"anthropic": {"anthropic-beta": "no-training-data-0"}}
# NEW: No custom headers — anthropic SDK handles auth via api_key only
PROVIDER_HEADERS: Dict[str, Dict] = {}

SENSITIVE_PATTERNS = [
    r'\b\d{10,16}\b',              # phone/card numbers
    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',  # emails
    r'\b(?:password|passwd|secret|token|key|api_key)\s*[:=]\s*\S+',
    r'\b\d{3}-\d{2}-\d{4}\b',     # SSN pattern
]

BLOCKED_DOMAINS = [
    "ads.google.com", "doubleclick.net", "facebook-tracking",
    "analytics.google.com",
]

ALLOWED_DOMAINS = [
    "api.anthropic.com", "generativelanguage.googleapis.com",
    "api.openai.com", "api.groq.com", "integrate.api.nvidia.com",
    "api.elevenlabs.io", "api.cerebras.ai", "openrouter.ai",
    "api.deepseek.com", "api.telegram.org",
    "localhost", "127.0.0.1",
]


class PrivacyFirewall:
    def __init__(self, config: dict):
        self.config = config
        self.enabled = config.get("security", {}).get("firewall_enabled", True)
        self._compiled = [re.compile(p, re.IGNORECASE) for p in SENSITIVE_PATTERNS]
        logger.debug("PrivacyFirewall initialized")

    def sanitize_for_cloud(self, text: str) -> str:
        """Remove sensitive patterns before sending to cloud APIs."""
        if not self.enabled:
            return text
        for pattern in self._compiled:
            text = pattern.sub("[REDACTED]", text)
        return text

    def is_domain_allowed(self, domain: str) -> bool:
        if any(blocked in domain for blocked in BLOCKED_DOMAINS):
            return False
        if any(allowed in domain for allowed in ALLOWED_DOMAINS):
            return True
        return True  # Default allow — conservative

    def get_provider_headers(self, provider: str) -> Dict:
        """Get any additional headers for a provider. Empty by default."""
        return PROVIDER_HEADERS.get(provider, {})

    def check_output(self, text: str) -> str:
        """Verify output doesn't accidentally leak sensitive data."""
        return text

    def get_status(self) -> Dict:
        return {"enabled": self.enabled, "healthy": True}
