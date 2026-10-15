"""
MANAGER OS — Creative Agent
════════════════════════════
FILE: agents/creative_agent.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
PURPOSE: All creative work — images, videos, writing, marketing.
         Output standard: looks and feels made by a skilled human professional.
         NOT generic AI output. Cinematic quality always.

DO NOT DELETE ANY CODE — comment out with reason and date
"""

from typing import Dict, Any
import os
import json
from loguru import logger
from agents.base_agent import BaseAgent
from core.poster_generator import generate_invite_poster


class CreativeAgent(BaseAgent):

    CREATIVE_SYSTEM = """
You are a world-class creative director with expertise in visual design,
copywriting, brand identity, and content creation.
Your work is always distinctive, polished, and memorable.
You never produce generic output. Every piece has a clear creative direction.
You think like: What will make this unforgettable? What's the one thing someone remembers?
Output standard: indistinguishable from work done by a skilled human professional.
"""

    async def execute(self, request: str, context: Dict[str, Any]) -> str:
        req_lower = request.lower()

        if any(w in req_lower for w in ["image", "photo", "picture", "visual", "logo", "poster"]):
            return await self._create_image_prompt(request, context)
        elif any(w in req_lower for w in ["video", "film", "cinematic", "animation"]):
            return await self._create_video_brief(request, context)
        elif any(w in req_lower for w in ["write", "article", "blog", "copy", "script"]):
            return await self._create_written_content(request, context)
        elif any(w in req_lower for w in ["brand", "identity", "name", "tagline"]):
            return await self._brand_creation(request, context)
        else:
            return await self._ask_ai(request, system=self.CREATIVE_SYSTEM, task_type="creative")

    async def _create_image_prompt(self, request: str, context: Dict) -> str:
        """Generate optimized image generation prompts or execute poster generation directly"""
        req_lower = request.lower()
        if any(w in req_lower for w in ["create", "generate", "make", "render", "design"]) and any(w in req_lower for w in ["poster", "invite", "invitation"]):
            logger.info("CreativeAgent: detected poster generation execution request")
            
            # Use AI to parse details out of the request
            parser_prompt = f"""
Analyze this event request: "{request}"
Generate a JSON object:
{{
  "title": "gorgeous short event title",
  "details": "Date: ...\nVenue: ...\nTime: ...\nRSVP: ...",
  "theme": "party/celebration/meeting/general"
}}
Return ONLY valid raw JSON. No markdown or other text.
"""
            try:
                raw_response = await self.router.complete(
                    system="You are a precise data extraction agent. You output ONLY valid raw JSON.",
                    messages=[{"role": "user", "content": parser_prompt}],
                    task_type="writing"
                )
                cleaned = raw_response.strip().replace("```json", "").replace("```", "").strip()
                data = json.loads(cleaned)
                title = data.get("title", "Invitation")
                details = data.get("details", "")
                theme = data.get("theme", "party")
            except Exception as e:
                logger.error(f"Failed to parse event details in CreativeAgent: {e}")
                title = "Event Invitation"
                details = request
                theme = "party"
                
            poster_path = os.path.abspath("./logs/creative_poster.png")
            try:
                await generate_invite_poster(title, details, theme, poster_path, self.config)
                return f"Sir, I have generated your custom invitation poster. You can find it at: {poster_path}"
            except Exception as ex:
                return f"Sir, I encountered an error rendering the poster: {ex}"

        # Otherwise fallback to standard text generation of prompts
        prompt = f"""
Create an optimized image generation prompt for: {request}

Provide prompts for multiple generators:

**DALL-E 3 Prompt:**
[Highly detailed, specific prompt. Include: subject, style, lighting, mood, composition, color palette, quality modifiers]

**Stable Diffusion / FLUX Prompt:**
[SD-optimized with quality tags: masterpiece, best quality, ultra-detailed, etc.]
[Negative prompt: what to exclude]

**Midjourney Prompt:**
[With aspect ratio --ar, style --style, quality --q parameters]

**Creative Direction:**
[What makes this image distinctive — the creative concept behind it]

**Alternative Concepts:**
[2-3 alternative directions if this doesn't match the vision]
"""
        return await self.router.complete(
            system=self.CREATIVE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="creative",
            max_tokens=1500
        )

    async def _create_video_brief(self, request: str, context: Dict) -> str:
        """Create video production brief for Runway ML / Kling AI"""
        prompt = f"""
Create a video production brief for: {request}

**RUNWAY ML PROMPT:**
[Exact text prompt for Runway Gen-3. Include: subject motion, camera movement, 
visual style, lighting changes, atmosphere. Be very specific about motion.]

**KLING AI PROMPT:**
[Optimized for Kling's strengths — character consistency, realistic motion]

**PRODUCTION BRIEF:**
- Duration: [recommended length]
- Style: [cinematic, documentary, commercial, artistic]
- Camera: [movements, angles, transitions]
- Mood: [atmospheric description]
- Color grade: [warm/cool/desaturated/vibrant + specific reference]
- Music mood: [for the final edit]

**STORYBOARD (text):**
Shot 1 (0-3s): [Description]
Shot 2 (3-8s): [Description]
[Continue]
"""
        return await self.router.complete(
            system=self.CREATIVE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="creative",
            max_tokens=2000
        )

    async def _create_written_content(self, request: str, context: Dict) -> str:
        """Create written content — articles, blogs, copy, scripts"""
        prompt = f"""
Create: {request}

Standards:
- Opening line must hook immediately — no slow introductions
- Every paragraph must earn its place — cut anything that doesn't serve the reader
- Specific over vague always — numbers, names, examples
- End with something memorable, not a generic conclusion
- Match the platform's tone and format

Provide the complete piece, ready to publish.
After the piece: [CRAFT NOTES] — brief note on the creative choices made.
"""
        return await self.router.complete(
            system=self.CREATIVE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="writing",
            max_tokens=3000
        )

    async def _brand_creation(self, request: str, context: Dict) -> str:
        """Brand identity creation"""
        prompt = f"""
Create brand identity for: {request}

**BRAND NAMES (5 options):**
For each: Name + why it works + domain availability check (.com, .in)

**TAGLINE OPTIONS (3):**
Short, memorable, captures the essence

**BRAND VOICE:**
- Personality: [3 adjectives]
- Tone: [how it speaks]
- What it never says/does

**VISUAL IDENTITY:**
- Color palette (with hex codes): Primary + Secondary + Accent
- Typography direction: [Heading font style] + [Body font style]
- Logo concept: [Describe 3 logo directions]
- Overall aesthetic: [1-2 sentence mood description]

**POSITIONING STATEMENT:**
"For [target audience] who [need/problem], [Brand Name] is [category] that [key benefit] 
because [reason to believe]."
"""
        return await self.router.complete(
            system=self.CREATIVE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="creative",
            max_tokens=2000
        )

    async def get_status(self) -> Dict:
        return {"healthy": True, "state": "running", "agent": "CreativeAgent"}
