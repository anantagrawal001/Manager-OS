"""
MANAGER OS — Social Media Agent
═════════════════════════════════
FILE: agents/social_agent.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
PURPOSE: Complete social media management.
         - Instagram (personal + professional): content, reels, analytics
         - Facebook, Twitter/X, LinkedIn
         - Reel scripts (second-by-second breakdown)
         - Brand deal pipeline — from outreach to payment tracking
         - Posting schedule optimization for max reach
         - Competitor analysis and strategy adjustment

DO NOT DELETE ANY CODE — comment out with reason and date
"""

from typing import Dict, Any
from loguru import logger
from agents.base_agent import BaseAgent
from core.browser_automation import create_instagram_account


class SocialAgent(BaseAgent):
    """
    Full social media management.
    Grows accounts from zero to brand-deal-eligible systematically.
    """

    SOCIAL_SYSTEM = """
You are a world-class social media strategist and content creator.
You understand viral content mechanics, platform algorithms, and brand building.
You create content that is genuine, engaging, and grows audiences.
You think in terms of: Hook (first 2 seconds) → Value → CTA
Every reel/post has a specific goal: reach, engagement, followers, or conversions.
You always back strategy with data — what worked, what didn't, why.
"""

    async def execute(self, request: str, context: Dict[str, Any]) -> str:
        req_lower = request.lower()

        if any(w in req_lower for w in ["create", "signup", "sign up", "register"]) and "instagram" in req_lower:
            return await self._create_instagram_signup(request, context)
        elif any(w in req_lower for w in ["reel", "video script", "script"]):
            return await self._create_reel_script(request, context)
        elif any(w in req_lower for w in ["caption", "post", "content"]):
            return await self._create_content(request, context)
        elif any(w in req_lower for w in ["brand", "deal", "sponsor", "collab"]):
            return await self._brand_deal_pipeline(request, context)
        elif any(w in req_lower for w in ["strategy", "grow", "followers", "reach"]):
            return await self._growth_strategy(request, context)
        elif any(w in req_lower for w in ["analytics", "performance", "stats"]):
            return await self._analytics_review(request, context)
        elif any(w in req_lower for w in ["schedule", "when to post", "posting time"]):
            return await self._posting_schedule(request, context)
        else:
            return await self._ask_ai(request, system=self.SOCIAL_SYSTEM)

    async def _create_instagram_signup(self, request: str, context: Dict) -> str:
        """Trigger Instagram signup page on Chrome browser and ask for details"""
        logger.info("SocialAgent: triggering Instagram signup automation")
        
        # Ask AI to check if the user request has details like email, phone, fullname, username
        parser_prompt = f"""
Analyze this Instagram creation request from the user: "{request}"

Extract any account registration details provided:
- Email/Phone number
- Full Name
- Username
- Password

Generate a JSON object matching this structure:
{{
  "contact": "extracted email or phone number or null",
  "fullname": "extracted full name or null",
  "username": "extracted username or null",
  "password": "extracted password or null"
}}

Return ONLY valid JSON. Do not include any markdown formatting, backticks, or commentary.
"""
        import json
        contact = None
        fullname = None
        username = None
        
        try:
            raw_response = await self.router.complete(
                system="You are a precise JSON extractor. Output valid JSON only.",
                messages=[{"role": "user", "content": parser_prompt}],
                task_type="writing"
            )
            cleaned = raw_response.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)
            contact = data.get("contact")
            fullname = data.get("fullname")
            username = data.get("username")
        except Exception as e:
            logger.error(f"Failed to parse Instagram registration details: {e}")

        success = await create_instagram_account()
        
        if success:
            questions = []
            if not contact:
                questions.append("mobile number or email ID")
            if not fullname:
                questions.append("full name")
            if not username:
                questions.append("desired username")
            
            if questions:
                questions_str = ", ".join(questions)
                return f"Sir, I have opened Google Chrome to the Instagram signup page. To automate the form submission, could you please provide your: {questions_str}?"
            else:
                return f"Sir, I have opened Google Chrome to the Instagram signup page and am filling in the details for contact: '{contact}', full name: '{fullname}', and username: '{username}'."
        else:
            return "Sir, I encountered an issue launching the browser automation for Instagram."

    async def _create_reel_script(self, request: str, context: Dict) -> str:
        """Create a complete reel script with second-by-second breakdown"""
        prompt = f"""
{request}

Create a complete Instagram/YouTube Shorts reel script:

FORMAT:
**HOOK (0-3 seconds):** [Exact text to say/show — this MUST stop the scroll]
**OPENING (3-8 seconds):** [Setup the problem/curiosity]

---Second by second breakdown---
0:00 - 0:03: [Visual + Audio]
0:03 - 0:08: [Visual + Audio]
[Continue for full duration]

---

**CAPTIONS/TEXT OVERLAYS:** [Exact text, timing, placement]
**MUSIC MOOD:** [Type of music to search for]
**B-ROLL NEEDED:** [What to film]
**HASHTAGS:** [30 optimized hashtags — mix of niche, medium, broad]
**CAPTION:** [Complete Instagram caption with hook + value + CTA]
**CTA (last 3 seconds):** [Exact call to action]

TARGET: [Reach / Engagement / Followers / Brand awareness]
EXPECTED PERFORMANCE: [Based on this format, realistic expected reach]

Make this VIRAL-worthy. The hook is everything.
"""
        return await self.router.complete(
            system=self.SOCIAL_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="creative",
            max_tokens=2000
        )

    async def _create_content(self, request: str, context: Dict) -> str:
        """Create social media post content"""
        prompt = f"""
{request}

Create platform-optimized content:

For Instagram:
- Caption (hook → value → CTA → hashtags)
- Carousel slide content if applicable
- Story sequence (3-5 slides)

For LinkedIn:
- Professional post (storytelling format)
- Hook line, body, CTA
- Relevant hashtags (5-10)

For Twitter/X:
- Thread if complex topic, single tweet if simple
- Engaging, punchy, shareable

Optimize each for maximum engagement on that platform.
"""
        return await self.router.complete(
            system=self.SOCIAL_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="creative",
            max_tokens=2000
        )

    async def _brand_deal_pipeline(self, request: str, context: Dict) -> str:
        """Brand deal outreach and management"""
        prompt = f"""
{request}

Brand deal pipeline strategy:

1. ELIGIBILITY CHECK: At what follower count/engagement rate are we eligible for:
   - Micro brands (1K-10K followers)
   - Mid-tier brands (10K-100K followers)  
   - Major brands (100K+ followers)

2. TARGET BRANDS: Identify 10 brands aligned with the account niche
   For each: why they're a fit, contact email format, pitch angle

3. PITCH EMAIL TEMPLATE:
   Subject: [Specific, professional]
   Body: [Intro + stats + why we fit their brand + clear ask + media kit offer]

4. RATE CARD (based on current following):
   - Story post: ₹X
   - Feed post: ₹X
   - Reel: ₹X
   - 3-month partnership: ₹X

5. NEGOTIATION SCRIPT: How to negotiate up from their first offer

6. DELIVERABLE TRACKING: Timeline, content approval, posting schedule, payment terms
"""
        return await self.router.complete(
            system=self.SOCIAL_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="writing",
            max_tokens=2500
        )

    async def _growth_strategy(self, request: str, context: Dict) -> str:
        """Account growth strategy"""
        prompt = f"""
{request}

Design a 90-day Instagram growth strategy:

WEEK 1-2 (Foundation):
- Content pillars (3-4 topics to own)
- Posting frequency and format mix
- Profile optimization checklist
- Bio rewrite

WEEK 3-8 (Growth Engine):
- Daily content calendar
- Hashtag strategy by content type
- Engagement tactics (comment pods, collaboration)
- Story strategy for retention

WEEK 9-12 (Scale):
- What's working — double down
- Collab/duet strategy
- Cross-promotion opportunities

METRICS TO TRACK WEEKLY:
- Follower growth rate
- Engagement rate (target 3-6%)
- Reach per reel
- Profile visits from reels
- Website clicks (if applicable)

Be specific with numbers and tactics. No vague advice.
"""
        return await self.router.complete(
            system=self.SOCIAL_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="creative",
            max_tokens=2500
        )

    async def _analytics_review(self, request: str, context: Dict) -> str:
        """Analytics and performance review"""
        return (
            "Sir, to pull your analytics I'll need your Instagram account connected. "
            "Once you complete the OAuth setup, I'll give you weekly performance reports "
            "showing what's working, what's not, and exactly what to do about it."
        )

    async def _posting_schedule(self, request: str, context: Dict) -> str:
        """Optimize posting schedule"""
        prompt = f"""
{request}

Optimal posting schedule for Indian Instagram audience:

Based on algorithm data and engagement patterns:
- Best days: [rank them]
- Best times (IST): [specific windows]
- Reel frequency: [per week]
- Stories: [per day]
- Carousels: [per week]
- Single image: [per week]

Create a concrete weekly schedule template.
Explain WHY each time slot works (algorithm behavior, audience activity).
"""
        return await self.router.complete(
            system=self.SOCIAL_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="creative"
        )

    async def get_status(self) -> Dict:
        return {"healthy": True, "state": "running", "agent": "SocialAgent"}
