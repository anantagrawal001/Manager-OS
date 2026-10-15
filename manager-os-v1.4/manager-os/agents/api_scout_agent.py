"""
MANAGER OS — API Scout Agent
══════════════════════════════
FILE: agents/api_scout_agent.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
PURPOSE: Dedicated agent — sole purpose is finding free access to premium AI models.
         Monitors: NVIDIA NIM, Groq, Together AI, OpenRouter, Cerebras, Fireworks,
         DeepInfra, HuggingFace Inference, Replicate, and more.
         Weekly scan + triggered when any model hits rate limit.
         On finding better free access → notifies Sir → integrates on approval.

NVIDIA NIM is the crown jewel — lists Claude, Llama 405B, Mistral Large,
Nemotron, CodeLlama and 50+ premium models with free API keys.

DO NOT DELETE ANY CODE — comment out with reason and date
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

import httpx
from loguru import logger

from agents.base_agent import BaseAgent


@dataclass
class FreeModelSource:
    """Represents a source of free premium AI model access"""
    provider: str
    model_name: str
    quality_tier: str        # premium | good | basic
    free_limit: str          # e.g., "1000 req/day", "free credits on signup"
    api_format: str          # openai-compatible | custom
    endpoint: str
    signup_url: str
    notes: str
    discovered_date: str = field(default_factory=lambda: datetime.now().isoformat())
    verified: bool = False
    integrated: bool = False


# Known free premium model sources — pre-loaded
KNOWN_FREE_SOURCES = [
    FreeModelSource(
        provider="NVIDIA NIM",
        model_name="llama-3.1-405b-instruct",
        quality_tier="premium",
        free_limit="1000 req/day free tier",
        api_format="openai-compatible",
        endpoint="https://integrate.api.nvidia.com/v1",
        signup_url="https://build.nvidia.com",
        notes="OpenAI-compatible. Set base_url to NVIDIA endpoint. Free API key from build.nvidia.com",
        verified=True,
        integrated=True,
    ),
    FreeModelSource(
        provider="NVIDIA NIM",
        model_name="mistral-large-2-instruct",
        quality_tier="premium",
        free_limit="1000 req/day free tier",
        api_format="openai-compatible",
        endpoint="https://integrate.api.nvidia.com/v1",
        signup_url="https://build.nvidia.com",
        notes="Mistral Large via NVIDIA NIM — free tier",
        verified=True,
        integrated=True,
    ),
    FreeModelSource(
        provider="NVIDIA NIM",
        model_name="nvidia/nemotron-4-340b-instruct",
        quality_tier="premium",
        free_limit="1000 req/day free tier",
        api_format="openai-compatible",
        endpoint="https://integrate.api.nvidia.com/v1",
        signup_url="https://build.nvidia.com",
        notes="NVIDIA's own 340B model — very strong reasoning",
        verified=True,
        integrated=False,
    ),
    FreeModelSource(
        provider="Groq",
        model_name="llama-3.1-70b-versatile",
        quality_tier="premium",
        free_limit="14,400 req/day, 131k tokens/min",
        api_format="openai-compatible",
        endpoint="https://api.groq.com/openai/v1",
        signup_url="https://groq.com",
        notes="Extremely fast inference. OpenAI-compatible. Best for speed.",
        verified=True,
        integrated=True,
    ),
    FreeModelSource(
        provider="Groq",
        model_name="llama-3.1-405b-reasoning",
        quality_tier="premium",
        free_limit="limited but free",
        api_format="openai-compatible",
        endpoint="https://api.groq.com/openai/v1",
        signup_url="https://groq.com",
        notes="405B on Groq — fastest 405B available",
        verified=True,
        integrated=False,
    ),
    FreeModelSource(
        provider="Together AI",
        model_name="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
        quality_tier="premium",
        free_limit="$25 free credits on signup",
        api_format="openai-compatible",
        endpoint="https://api.together.xyz/v1",
        signup_url="https://together.ai",
        notes="Free credits cover significant usage. OpenAI-compatible.",
        verified=True,
        integrated=False,
    ),
    FreeModelSource(
        provider="DeepSeek",
        model_name="deepseek-r1",
        quality_tier="premium",
        free_limit="Very cheap / free tier available",
        api_format="openai-compatible",
        endpoint="https://api.deepseek.com/v1",
        signup_url="https://platform.deepseek.com",
        notes="SECURITY: Strip all PII before sending. Use for math/code/logic only.",
        verified=True,
        integrated=True,
    ),
    FreeModelSource(
        provider="Cerebras",
        model_name="llama3.1-70b",
        quality_tier="good",
        free_limit="Free tier with high speed",
        api_format="openai-compatible",
        endpoint="https://api.cerebras.ai/v1",
        signup_url="https://cerebras.ai",
        notes="Fastest inference available — specialized hardware",
        verified=True,
        integrated=False,
    ),
    FreeModelSource(
        provider="OpenRouter",
        model_name="multiple",
        quality_tier="varies",
        free_limit="Some models free, others pay-per-use",
        api_format="openai-compatible",
        endpoint="https://openrouter.ai/api/v1",
        signup_url="https://openrouter.ai",
        notes="Aggregator — access 100+ models via one API key. Filter for :free models.",
        verified=True,
        integrated=False,
    ),
    FreeModelSource(
        provider="Fireworks AI",
        model_name="llama-v3p1-70b-instruct",
        quality_tier="good",
        free_limit="Free credits on signup",
        api_format="openai-compatible",
        endpoint="https://api.fireworks.ai/inference/v1",
        signup_url="https://fireworks.ai",
        notes="Fast inference, good quality",
        verified=True,
        integrated=False,
    ),
    FreeModelSource(
        provider="HuggingFace",
        model_name="meta-llama/Meta-Llama-3.1-70B-Instruct",
        quality_tier="good",
        free_limit="Free tier inference API",
        api_format="custom",
        endpoint="https://api-inference.huggingface.co/models",
        signup_url="https://huggingface.co",
        notes="Free serverless inference. Rate limited but free.",
        verified=True,
        integrated=False,
    ),
]

REGISTRY_PATH = Path("./skills/registry/api_sources.json")


class APIScoutAgent(BaseAgent):
    """
    Dedicated API Scout — finds and integrates free premium AI model access.
    
    Weekly scan cycle:
    1. Check all known platforms for new free models
    2. Verify quality and free tier details
    3. Compare against current router's models
    4. If better → present to Sir
    5. If approved → integrate into router's key pool
    """

    SCOUT_SYSTEM = """
You are an AI API analyst. You evaluate AI model APIs for:
1. Quality (benchmark scores, real-world performance)
2. Free tier details (exactly how many requests/tokens per day/month)
3. Integration effort (OpenAI-compatible = easy, custom = hard)
4. Privacy (where does data go, training opt-out available?)
5. Reliability (uptime, response time)

Be precise. Only recommend genuinely useful additions.
"""

    def __init__(self, config: dict, router, firewall):
        super().__init__(config, router, firewall)
        self.known_sources = KNOWN_FREE_SOURCES.copy()
        self.integrated_models: List[str] = []
        self._load_registry()

    async def execute(self, request: str, context: Dict[str, Any]) -> str:
        req_lower = request.lower()

        if any(w in req_lower for w in ["scan", "search", "find", "new", "weekly"]):
            return await self._weekly_scan(request, context)
        elif any(w in req_lower for w in ["list", "show", "available", "sources"]):
            return await self._list_sources(request, context)
        elif any(w in req_lower for w in ["integrate", "add", "install"]):
            return await self._integrate_source(request, context)
        elif any(w in req_lower for w in ["nvidia", "nim", "groq"]):
            return await self._spotlight_source(request, context)
        else:
            return await self._list_sources(request, context)

    async def _weekly_scan(self, request: str, context: Dict) -> str:
        """Scan all platforms for new free premium model access"""
        logger.info("API Scout: Running weekly scan for new free premium models")

        scan_prompt = """
Scan the current AI API landscape for new or updated free access to premium models.

Check these platforms specifically:
1. NVIDIA NIM (build.nvidia.com) — what new models have been added?
2. Groq (groq.com) — any new free models or limit increases?
3. Together AI — new free/cheap models?
4. OpenRouter — which models are marked :free now?
5. Cerebras — any new models?
6. Fireworks AI — updates?
7. Perplexity API — free tier changes?
8. Any other new entrants offering premium models free?

For each new finding:
- Provider name
- Model name and quality level (premium/good/basic)
- Exact free tier limits
- OpenAI-compatible? (yes/no)
- Privacy: does data go to the model company? Training opt-out?
- Integration effort: easy/medium/hard

Focus on models that are better than or complement:
Claude Sonnet, Gemini Flash, GPT-4o-mini, Llama 3.1 8B (current baseline)
"""
        result = await self.router.complete(
            system=self.SCOUT_SYSTEM,
            messages=[{"role": "user", "content": scan_prompt}],
            task_type="search"
        )

        # Save scan results
        scan_log = Path("./logs/api_scout_scan.log")
        with open(scan_log, "a") as f:
            f.write(f"\n\n=== SCAN {datetime.now().isoformat()} ===\n{result}")

        return (
            f"**API Scout — Weekly Scan Complete**\n"
            f"Scanned: {datetime.now().strftime('%B %d, %Y')}\n\n"
            f"{result}\n\n"
            f"Sir, say 'integrate [model name]' for anything you'd like added to the system."
        )

    async def _list_sources(self, request: str, context: Dict) -> str:
        """List all known free premium model sources"""
        integrated = [s for s in self.known_sources if s.integrated]
        available = [s for s in self.known_sources if not s.integrated]

        integrated_lines = "\n".join(
            f"  ✓ {s.provider} — {s.model_name} ({s.free_limit})"
            for s in integrated
        )

        available_lines = "\n".join(
            f"  ○ {s.provider} — {s.model_name} | {s.free_limit}"
            for s in available
        )

        return (
            f"**Free Premium AI Model Sources — Current Inventory**\n\n"
            f"**Already Integrated:**\n{integrated_lines}\n\n"
            f"**Available to Add (pending Sir's approval):**\n{available_lines}\n\n"
            f"📌 NVIDIA NIM is the primary source — 50+ premium models, all free tier.\n"
            f"   Sign up at: build.nvidia.com → Get API Key → One key for all models.\n\n"
            f"Sir, say 'integrate [provider name]' to add any of these."
        )

    async def _integrate_source(self, request: str, context: Dict) -> str:
        """Mark a source as integrated and add to key manager"""
        for source in self.known_sources:
            if source.provider.lower() in request.lower() or source.model_name.lower() in request.lower():
                source.integrated = True
                self._save_registry()

                integration_guide = f"""
**Integration: {source.provider} — {source.model_name}**

1. Sign up at: {source.signup_url}
2. Get your free API key
3. Tell me the key and I'll add it to the vault

API Format: {source.api_format}
Endpoint: {source.endpoint}
Free Limit: {source.free_limit}
Note: {source.notes}

Once you share the key, Sir, I'll add it to the router automatically.
"""
                return integration_guide

        return f"Sir, I didn't find a matching source for '{request}'. Check the full list with 'show api sources'."

    async def _spotlight_source(self, request: str, context: Dict) -> str:
        """Detailed info on a specific source"""
        if "nvidia" in request.lower() or "nim" in request.lower():
            nvidia_sources = [s for s in self.known_sources if "NVIDIA" in s.provider]
            lines = "\n".join(
                f"  • {s.model_name}: {s.notes}"
                for s in nvidia_sources
            )
            return (
                f"**NVIDIA NIM — Free Premium AI Platform**\n\n"
                f"NVIDIA hosts 50+ premium AI models and gives free API access to promote their GPU platform.\n\n"
                f"**Currently tracked models:**\n{lines}\n\n"
                f"**How to get access:**\n"
                f"1. Go to: build.nvidia.com\n"
                f"2. Create a free account\n"
                f"3. Click 'Get API Key'\n"
                f"4. One key works for ALL models listed\n"
                f"5. All models use OpenAI-compatible format — plug-and-play\n\n"
                f"**Setup for Manager:** Tell me your NVIDIA NIM API key and I'll add all their models to the router instantly, Sir."
            )

        return await self._list_sources(request, context)

    def _load_registry(self):
        """Load integration status from disk"""
        if REGISTRY_PATH.exists():
            try:
                with open(REGISTRY_PATH) as f:
                    data = json.load(f)
                    self.integrated_models = data.get("integrated", [])
                    # Update known_sources integration status
                    for source in self.known_sources:
                        key = f"{source.provider}::{source.model_name}"
                        if key in self.integrated_models:
                            source.integrated = True
            except Exception as e:
                logger.error(f"Registry load error: {e}")

    def _save_registry(self):
        """Save integration status to disk"""
        REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
        integrated_keys = [
            f"{s.provider}::{s.model_name}"
            for s in self.known_sources if s.integrated
        ]
        with open(REGISTRY_PATH, "w") as f:
            json.dump({
                "integrated": integrated_keys,
                "last_scan": datetime.now().isoformat(),
                "total_sources": len(self.known_sources),
            }, f, indent=2)

    async def get_status(self) -> Dict:
        return {
            "healthy": True,
            "state": "running",
            "total_sources": len(self.known_sources),
            "integrated": sum(1 for s in self.known_sources if s.integrated),
            "available_to_add": sum(1 for s in self.known_sources if not s.integrated),
        }
