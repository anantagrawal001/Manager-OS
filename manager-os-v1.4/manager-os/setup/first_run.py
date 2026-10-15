"""
MANAGER OS - First Run Setup
==============================
FILE: setup/first_run.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
PURPOSE: Orchestrates the complete first-run setup sequence.
         Called by SETUP.bat. Handles everything Anant doesn't need to do manually.

SEQUENCE:
  1. Install Python dependencies
  2. Install Playwright + Chromium
  3. Install Ollama + pull AI models (background)
  4. Create database tables
  5. Setup encrypted key vault
  6. Run API key auto-fetcher
  7. Voice enrollment
  8. Hardware fingerprint capture
  9. Tailscale setup
  10. Launch Manager OS

DO NOT DELETE ANY CODE - comment out with reason and date
"""

import asyncio
import subprocess
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def print_banner():
    banner = """
+--------------------------------------------------------------+
|                                                              |
|              M A N A G E R   O S                             |
|              First Run Setup                                 |
|                                                              |
|              Built exclusively for Anant                     |
|                                                              |
+--------------------------------------------------------------+
"""
    print(banner)


async def step(number: int, description: str, fn):
    """Run a setup step with progress indicator"""
    print(f"\n  [{number}] {description}...", end=" ", flush=True)
    try:
        if asyncio.iscoroutinefunction(fn):
            await fn()
        else:
            fn()
        print("OK")
        return True
    except Exception as e:
        print(f"FAIL - {e}")
        return False


async def install_dependencies():
    """Install Python packages from requirements.txt"""
    req_file = Path("requirements.txt")
    if not req_file.exists():
        raise FileNotFoundError("requirements.txt not found")

    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", "requirements.txt",
         "--quiet", "--break-system-packages"],
        check=True, capture_output=True
    )


async def install_playwright():
    """Install Playwright and download Chromium"""
    subprocess.run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        check=True, capture_output=True
    )


async def setup_ollama():
    """Install Ollama and pull AI models in background"""
    # Check if Ollama installed
    try:
        result = subprocess.run(["ollama", "version"], capture_output=True, timeout=5)
        if result.returncode == 0:
            print("(Ollama already installed) ", end="")
    except FileNotFoundError:
        # Download and install Ollama for Windows
        print("(downloading Ollama) ", end="", flush=True)
        import urllib.request
        ollama_url = "https://ollama.com/download/ollama-windows-amd64.zip"
        ollama_zip = Path("./setup/ollama.zip")
        ollama_zip.parent.mkdir(exist_ok=True)
        urllib.request.urlretrieve(ollama_url, ollama_zip)

        import zipfile
        with zipfile.ZipFile(ollama_zip, 'r') as z:
            z.extractall("C:\\Program Files\\Ollama")

        os.environ["PATH"] += ";C:\\Program Files\\Ollama"

    # Pull models in background (don't block setup)
    print("(pulling AI models in background) ", end="", flush=True)
    asyncio.create_task(_pull_ollama_models())


async def _pull_ollama_models():
    """Pull Ollama models in background"""
    models = ["llama3.1:8b", "mistral:7b", "nomic-embed-text"]
    for model in models:
        try:
            subprocess.run(["ollama", "pull", model], capture_output=True)
        except Exception as e:
            pass  # Non-blocking — models downloaded when first needed


async def setup_database():
    """Create database tables"""
    from core.memory import MemoryManager
    import yaml
    with open("config.yaml") as f:
        config = yaml.safe_load(f)
    memory = MemoryManager(config)
    await memory.initialize()
    await memory.close()


def setup_directories():
    """Create all required directories"""
    dirs = [
        "./logs", "./backups", "./security/identity",
        "./security/voice_prints", "./skills/registry",
        "./setup"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)


async def run_api_key_setup():
    """Run API key auto-fetcher"""
    try:
        import yaml
        from core.key_manager import KeyManager
        from setup.api_key_fetcher import APIKeyFetcher

        with open("config.yaml") as f:
            config = yaml.safe_load(f)

        key_manager = KeyManager(config)
        fetcher = APIKeyFetcher(key_manager)
        await fetcher.run()
    except Exception as e:
        print(f"\n  (API key setup can be completed later — {e})", flush=True)


async def run_voice_enrollment():
    """Voice enrollment for identity verification"""
    try:
        import yaml
        from core.voice import VoiceEngine
        from core.identity import IdentityGuard

        with open("config.yaml") as f:
            config = yaml.safe_load(f)

        identity = IdentityGuard(config)
        await identity.enroll()
    except Exception as e:
        print(f"\n  (Voice enrollment can be done on first launch — {e})", flush=True)


async def setup_tailscale():
    """Setup Tailscale for remote access"""
    try:
        import yaml
        from security.tunnel import TailscaleManager

        with open("config.yaml") as f:
            config = yaml.safe_load(f)

        config["vpn"]["enabled"] = True
        tunnel = TailscaleManager(config)
        await tunnel.setup()
    except Exception as e:
        print(f"\n  (Tailscale setup can be done later — {e})", flush=True)


# Superseded 2026-10-12: retained for rollback; corrected implementation below.
# async def main():
#     print_banner()
#     print("  Setting up Manager OS - Sir, this will take a few minutes.\n")
#     print("  " + "-" * 56)
#
#     steps = [
#         (1, "Creating directory structure", setup_directories),
#         (2, "Installing Python dependencies", install_dependencies),
#         (3, "Setting up browser automation (Playwright)", install_playwright),
#         (4, "Setting up local AI models (Ollama)", setup_ollama),
#         (5, "Initializing database", setup_database),
#         (6, "Fetching API keys from providers", run_api_key_setup),
#         (7, "Enrolling voice identity", run_voice_enrollment),
#         (8, "Setting up remote access (Tailscale)", setup_tailscale),
#     ]
#
#     results = []
#     for number, description, fn in steps:
#         success = await step(number, description, fn)
#         results.append(success)
#
#     print("\n  " + "-" * 56)
#     passed = sum(results)
#     total = len(results)
#     print(f"\n  Setup complete: {passed}/{total} steps successful")
#
#     if passed >= 5:  # Core steps passed
#         print("\n  Manager OS is ready, Sir.")
#         print("  Run startup.bat to launch.\n")
#     else:
#         print("\n  Some setup steps failed. Manager OS will still launch")
#         print("  but some features may need configuration. Run startup.bat.\n")

async def main():
    # Preserve existing credentials and use the reliable core installer.
    import subprocess, sys
    from pathlib import Path
    result = subprocess.run([sys.executable, str(Path(__file__).with_name('bootstrap.py'))])
    if result.returncode:
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    asyncio.run(main())
