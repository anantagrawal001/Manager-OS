"""
MANAGER OS — API Key Fetcher
FILE: setup/api_key_fetcher.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
UPDATED: 2026-05-31 | Phase B (P1-9)
CHANGE P1-9: Validate non-empty key before saving. Prompt re-entry if empty.
             Skip button was causing empty strings to be saved as "valid" keys.
DO NOT DELETE — comment out with reason and date
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger


def open_in_chrome(url: str):
    """Open a URL in Google Chrome browser (not Chromium) on Windows/OSX/Linux."""
    import subprocess
    import os
    import webbrowser

    # Common Chrome installation paths on Windows
    chrome_paths = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ]

    for path in chrome_paths:
        if os.path.exists(path):
            try:
                subprocess.Popen([path, url])
                return True
            except Exception:
                pass

    # Fallback to webbrowser registry registration for chrome
    try:
        webbrowser.register('chrome', None, webbrowser.BackgroundBrowser("chrome"))
        chrome = webbrowser.get('chrome')
        chrome.open(url)
        return True
    except Exception:
        pass

    # Fallback to system command start chrome
    try:
        os.system(f'start chrome "{url}"')
        return True
    except Exception:
        pass

    # Final fallback to default system browser
    try:
        webbrowser.open(url)
        return True
    except Exception:
        return False


PROVIDERS = [
    {
        "name": "anthropic",
        "display": "Anthropic (Claude)",
        "url": "https://console.anthropic.com/settings/keys",
        "hint": "Starts with sk-ant-",
        "min_length": 20,
        "required": False,
    },
    {
        "name": "google",
        "display": "Google AI Studio (Gemini)",
        "url": "https://aistudio.google.com/apikey",
        "hint": "Starts with AIza",
        "min_length": 20,
        "required": False,
    },
    {
        "name": "groq",
        "display": "Groq (Fast free — RECOMMENDED)",
        "url": "https://console.groq.com/keys",
        "hint": "Starts with gsk_",
        "min_length": 20,
        "required": False,
    },
    {
        "name": "nvidia",
        "display": "NVIDIA NIM (50+ free premium models)",
        "url": "https://build.nvidia.com/",
        "hint": "Click 'Get API Key' on any model page",
        "min_length": 20,
        "required": False,
    },
    {
        "name": "openai",
        "display": "OpenAI (GPT fallback)",
        "url": "https://platform.openai.com/api-keys",
        "hint": "Starts with sk-",
        "min_length": 20,
        "required": False,
    },
    {
        "name": "elevenlabs",
        "display": "ElevenLabs (Premium voice)",
        "url": "https://elevenlabs.io/app/settings/api-keys",
        "hint": "32-character hex string",
        "min_length": 16,
        "required": False,
    },
    {
        "name": "huggingface",
        "display": "HuggingFace (Open source models)",
        "url": "https://huggingface.co/settings/tokens",
        "hint": "Starts with hf_",
        "min_length": 8,
        "required": False,
    },
]


class APIKeyFetcher:
    def __init__(self, key_manager):
        self.key_manager = key_manager
        self.saved_count = 0

    async def run(self):
        if os.environ.get("SETUP_UNATTENDED") == "1":
            print("\n[Manager] Unattended setup active. Skipping interactive API key configuration.")
            return

        print("\n" + "=" * 60)
        print("  MANAGER OS — API KEY SETUP")
        print("=" * 60)
        print("\nSir, I'll help you set up your API keys.")
        print("All keys are FREE — no credit card needed for most.")
        print("\nFor each provider:")
        print("  1. A browser tab will open (or visit the URL)")
        print("  2. Log in and create/copy your API key")
        print("  3. Paste it here when prompted")
        print("  4. Press Enter to skip any provider")
        print()

        for provider in PROVIDERS:
            await self._fetch_provider_key(provider)

        print(f"\n[Manager] API setup complete. {self.saved_count} provider(s) configured.")
        if self.saved_count == 0:
            print("[Manager] No keys saved — Manager will use Ollama local AI.")
        print("[Manager] Sir, you're all set. Starting Manager OS...\n")

    async def _fetch_provider_key(self, provider: dict):
        name = provider["name"]
        display = provider["display"]
        url = provider["url"]
        hint = provider["hint"]
        min_len = provider.get("min_length", 8)

        print(f"\n[Manager] Opening {display}...")
        print(f"          URL: {url}")
        print(f"          Hint: {hint}")

        # Try to open browser
        # OLD (2026-05-24): webbrowser.open(url) opened system default (which might be Chromium)
        # try:
        #     import webbrowser
        #     webbrowser.open(url)
        # except Exception:
        #     pass
        # NEW (2026-06-05): Use open_in_chrome to explicitly target Google Chrome
        open_in_chrome(url)

        input(f"\n[Manager] Sir, please log in and get your API key.\n"
              f"          Press ENTER when you're ready to paste it...")

        # P1-9: Retry loop — don't accept empty or too-short keys
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                key = input(f"[Manager] Paste your {display} API key (or press Enter to skip): ").strip()
            except (EOFError, KeyboardInterrupt):
                print(f"\n  ○ {display} — skipped")
                return

            # P1-9: Validate non-empty
            if not key:
                print(f"  ○ {display} — skipped")
                return

            # P1-9: Validate minimum length
            if len(key) < min_len:
                print(f"  ✗ Key seems too short (got {len(key)} chars, expected ≥{min_len}).")
                if attempt < max_attempts - 1:
                    print(f"    Try again or press Enter to skip.")
                    continue
                else:
                    print(f"  ○ {display} — skipped after {max_attempts} attempts")
                    return

            # P1-9: Check for placeholder/test values
            if key.lower() in ("none", "null", "test", "your_key_here", "api_key"):
                print(f"  ✗ That looks like a placeholder, not a real key. Skipping.")
                return

            # Key looks valid — save it
            try:
                self.key_manager.add_key(name, key, "setup_run")
                print(f"  ✓ {display} — key saved")
                self.saved_count += 1
                return
            except Exception as e:
                logger.error(f"Key save error for {name}: {e}")
                print(f"  ✗ Failed to save key: {e}")
                return
