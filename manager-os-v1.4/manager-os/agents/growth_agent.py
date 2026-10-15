"""
MANAGER OS — Growth Agent (Self-Upgrade Engine)
═════════════════════════════════════════════════
FILE: agents/growth_agent.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
PURPOSE: Self-upgrade engine. Every Monday scans for new AI tools, models, APIs.
         When finds something useful → presents to Sir with explanation.
         If Sir says yes → integrates it as new skill.
         Manager never stays static. Always growing.

DO NOT DELETE ANY CODE — comment out with reason and date
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
from loguru import logger
from agents.base_agent import BaseAgent


class GrowthAgent(BaseAgent):
    """
    Self-upgrade engine.
    Monitors AI landscape weekly. Proposes new capabilities. Installs on approval.
    """

    GROWTH_SYSTEM = """
You are an AI technology scout. You track the AI landscape obsessively.
You evaluate new tools by: practical value to the user, free tier availability,
integration complexity, and quality vs existing solutions.
You never recommend something that isn't genuinely better than what exists.
"""

    SKILLS_REGISTRY = Path("./skills/registry/installed_skills.json")

    async def execute(self, request: str, context: Dict[str, Any]) -> str:
        req_lower = request.lower()

        if any(w in req_lower for w in ["scan", "new tools", "updates", "weekly"]):
            return await self._weekly_scan(request, context)
        elif any(w in req_lower for w in ["install", "add skill", "integrate"]):
            return await self._install_skill(request, context)
        elif any(w in req_lower for w in ["skills", "capabilities", "what can you"]):
            return await self._list_skills(request, context)
        else:
            return await self._ask_ai(request, system=self.GROWTH_SYSTEM)

    async def _weekly_scan(self, request: str, context: Dict) -> str:
        """Scan for new AI tools and capabilities"""
        prompt = """
You are scanning the AI landscape for tools released or significantly updated in the past week.

Identify the top 3-5 most practically useful new developments for a personal AI system that:
- Manages trading, careers, social media, creative work, and daily life
- Runs on a consumer laptop (RTX 5060, 16GB RAM)
- Prefers free or very cheap tools
- Values quality and reliability

For each tool/update:
1. NAME and what it does
2. Why it's better than current alternatives
3. Free tier details
4. Integration difficulty (Easy/Medium/Hard)
5. Recommended: YES/NO and why

Format as a clear briefing. Be honest about what's not worth adding.
"""
        result = await self.router.complete(
            system=self.GROWTH_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="search"
        )

        return (
            f"**Weekly AI Landscape Scan — {datetime.now().strftime('%B %d, %Y')}**\n\n"
            f"{result}\n\n"
            f"Sir, for any of these you'd like to add, just say 'yes, install [name]' and I'll integrate it."
        )

    async def _install_skill(self, request: str, context: Dict) -> str:
        """Install a new skill/capability"""
        prompt = f"""
Anant wants to add this capability: {request}

Provide:
1. INTEGRATION PLAN: How to add this to Manager OS
2. FILES TO CREATE/MODIFY: Specific changes needed
3. DEPENDENCIES: New packages required
4. CONFIGURATION: Any API keys or setup needed
5. TESTING: How to verify it works

Also update the skills registry to record this new capability.
"""
        result = await self.router.complete(
            system=self.GROWTH_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="code"
        )

        # Log to skills registry
        await self._log_skill(request, result)

        return result

    async def _list_skills(self, request: str, context: Dict) -> str:
        """List all installed skills and capabilities"""
        skills = await self._load_skills()

        built_in = [
            "Voice interface (Whisper STT + Edge TTS)",
            "Multi-AI routing (Claude, Gemini, GPT, Ollama local)",
            "Trading analysis + multi-agent consensus",
            "Resume tailoring (Google XYZ formula + ATS)",
            "Job search + cold email automation",
            "Instagram/social media management",
            "Reel script creation",
            "Brand deal pipeline",
            "App + software building (any language)",
            "n8n workflow design",
            "Image generation (DALL-E, Flux, Stable Diffusion)",
            "Video production briefs (Runway, Kling)",
            "Content writing (articles, scripts, copy)",
            "Brand identity creation",
            "Gmail + WhatsApp + call management",
            "Morning briefing + life planning",
            "File system access",
            "Self-upgrade scanner",
        ]

        skills_list = "\n".join(f"  ✓ {s}" for s in built_in)

        added_list = ""
        if skills:
            added = "\n".join(f"  ✓ {s['name']} (added {s['date']})" for s in skills)
            added_list = f"\n\n**Added by Sir:**\n{added}"

        return (
            f"Sir, here's everything I can currently do:\n\n"
            f"**Built-in capabilities:**\n{skills_list}"
            f"{added_list}\n\n"
            f"New skills are added every Monday after the weekly scan, or anytime you ask."
        )

    async def _log_skill(self, description: str, plan: str):
        """Log a newly installed skill"""
        self.SKILLS_REGISTRY.parent.mkdir(parents=True, exist_ok=True)

        skills = await self._load_skills()
        skills.append({
            "name": description[:50],
            "date": datetime.now().strftime("%Y-%m-%d"),
            "description": description,
        })

        with open(self.SKILLS_REGISTRY, "w") as f:
            json.dump(skills, f, indent=2)

    async def _load_skills(self) -> List[Dict]:
        """Load skills registry"""
        if not self.SKILLS_REGISTRY.exists():
            return []
        try:
            with open(self.SKILLS_REGISTRY) as f:
                return json.load(f)
        except Exception:
            return []

    async def get_status(self) -> Dict:
        skills = await self._load_skills()
        return {
            "healthy": True,
            "state": "running",
            "installed_skills": len(skills),
        }
