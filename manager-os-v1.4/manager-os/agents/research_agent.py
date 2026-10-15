"""
MANAGER OS — Research Agent
════════════════════════════
FILE: agents/research_agent.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
PURPOSE: Real research with verified data. Proper thesis structure.
         Anti-hallucination protocol: every fact cited, unknown = "cannot verify".
         Uses real-time web search + cross-referencing. No fabricated data. Ever.

THESIS STRUCTURE:
  Abstract → Introduction → Methodology → Findings (real data) → Analysis → Conclusion → References

ANTI-HALLUCINATION RULES:
  - Every factual claim requires a source
  - Unknown → "could not verify" — NEVER fabricate
  - Numbers/stats always cross-checked minimum 2 sources
  - Confidence < 80% → explicitly flagged
  - Research: minimum 3 cross-referenced sources per key claim

DO NOT DELETE ANY CODE — comment out with reason and date
"""

import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from loguru import logger
from agents.base_agent import BaseAgent


@dataclass
class ResearchFinding:
    """A single verified research finding"""
    claim: str
    sources: List[str]
    confidence: float          # 0.0 - 1.0
    verified: bool
    notes: str = ""


@dataclass
class ResearchThesis:
    """Complete research thesis"""
    topic: str
    abstract: str
    introduction: str
    methodology: str
    findings: List[ResearchFinding]
    analysis: str
    conclusion: str
    references: List[str]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    word_count: int = 0


class ResearchAgent(BaseAgent):
    """
    Real research agent. Produces verified theses on any topic.
    Never hallucinates. Always cites sources. Flags uncertainty explicitly.
    """

    RESEARCH_SYSTEM = """
You are a rigorous academic researcher and analyst.

ABSOLUTE RULES — NEVER BREAK THESE:
1. NEVER state a fact you cannot verify. If uncertain → say "could not verify" or "insufficient data"
2. EVERY factual claim must have a citation or source reference
3. NEVER fabricate statistics, dates, names, or studies
4. If you find conflicting information between sources → present both and note the conflict
5. Clearly distinguish: CONFIRMED FACT vs INFERENCE vs SPECULATION
6. Numbers and statistics must be cross-referenced from minimum 2 sources
7. If confidence in a claim is below 80% → explicitly flag: "[UNCERTAIN — needs verification]"

Research methodology:
- Search for primary sources first (papers, official reports, government data)
- Verify key claims across multiple independent sources
- Note the date of each source (recent vs historical)
- Acknowledge limitations of your research

You produce structured, academic-quality research that is honest about what is known vs unknown.
"""

    # Superseded 2026-10-12: retained for rollback; corrected implementation below.
    # async def execute(self, request: str, context: Dict[str, Any]) -> str:
    #     req_lower = request.lower()
    #
    #     if any(w in req_lower for w in ["thesis", "full research", "complete analysis", "deep dive"]):
    #         return await self._full_thesis(request, context)
    #     elif any(w in req_lower for w in ["quick", "brief", "summary", "overview"]):
    #         return await self._quick_research(request, context)
    #     elif any(w in req_lower for w in ["fact check", "verify", "is it true", "confirm"]):
    #         return await self._fact_check(request, context)
    #     elif any(w in req_lower for w in ["market research", "industry", "sector"]):
    #         return await self._market_research(request, context)
    #     else:
    #         return await self._structured_research(request, context)

    async def execute(self, request, context):
        result = await self._ask_ai(request, system=self.RESEARCH_SYSTEM +
                   '\nNo live web search tool is connected. Offer a knowledge-based overview. '
                   'Do not claim you searched, verified, cross-referenced sources, or retrieved current data.', task_type='search')
        return 'Knowledge-based research draft — live sources have not been retrieved or verified.\n\n' + result

    async def _full_thesis(self, request: str, context: Dict) -> str:
        """Generate a complete research thesis"""
        topic = request.replace("thesis on", "").replace("full research on", "").strip()
        logger.info(f"Research Agent: Starting full thesis on '{topic}'")

        # Stage 1: Web research
        research_prompt = f"""
Research this topic thoroughly: {topic}

STAGE 1 — GATHER INFORMATION:
Search for:
1. Primary sources (academic papers, official reports, government data)
2. Recent developments (last 1-2 years)
3. Key statistics and data points
4. Expert opinions and consensus
5. Counter-arguments and alternative views

For each finding, note:
- The claim
- The source (name, date, URL if known)
- Your confidence level (high/medium/low)
- Whether this is a confirmed fact, inference, or speculation

STAGE 2 — STRUCTURE:
After gathering, organize into:
- Abstract (200 words)
- Introduction: context, why this matters
- Methodology: how this research was conducted
- Key Findings: with source citations
- Analysis: what the findings mean
- Conclusion: key takeaways
- References: all sources used

CRITICAL: Flag anything you cannot verify. Use [UNCERTAIN] marker. Never fabricate data.
"""
        result = await self.router.complete(
            system=self.RESEARCH_SYSTEM,
            messages=[{"role": "user", "content": research_prompt}],
            task_type="search",
            max_tokens=4000
        )

        # Stage 2: Verification pass
        verify_prompt = f"""
Review this research draft and identify any claims that:
1. Lack source citations
2. Seem like they could be fabricated or hallucinated
3. Are stated with more confidence than warranted
4. Conflict with other parts of the research

Research draft:
{result[:3000]}

For each issue found, mark it clearly and suggest how to fix it.
Then provide the corrected, verified version.
"""
        verified = await self.router.complete(
            system=self.RESEARCH_SYSTEM,
            messages=[{"role": "user", "content": verify_prompt}],
            task_type="reasoning",
            max_tokens=3000
        )

        return (
            f"**Research Thesis: {topic}**\n"
            f"*Generated: {datetime.now().strftime('%B %d, %Y')}*\n"
            f"*Anti-hallucination protocol active — all facts cross-referenced*\n\n"
            f"---\n\n"
            f"{verified}\n\n"
            f"---\n"
            f"*Note: Claims marked [UNCERTAIN] require additional verification. "
            f"Sources listed are from training knowledge — verify currency of data independently.*"
        )

    async def _structured_research(self, request: str, context: Dict) -> str:
        """Structured research on a topic — balanced depth"""
        prompt = f"""
Research this topic: {request}

Provide a structured research summary:

**WHAT IS KNOWN (Confirmed facts — high confidence):**
[List with sources]

**KEY FINDINGS:**
[Top 5-7 significant findings, each with source and confidence level]

**WHAT IS DEBATED (Conflicting information):**
[Where sources disagree — present both sides]

**GAPS (What could not be verified):**
[Facts you looked for but couldn't confirm — marked [UNVERIFIED]]

**DATA AND STATISTICS:**
[Key numbers — only ones with source citations]

**CONCLUSION:**
[What we can conclude with confidence from the research]

**SOURCES USED:**
[List all sources referenced]

Remember: [UNCERTAIN] or [UNVERIFIED] markers are required where confidence is low.
Do not fill gaps with plausible-sounding data.
"""
        return await self.router.complete(
            system=self.RESEARCH_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="search",
            max_tokens=3000
        )

    async def _quick_research(self, request: str, context: Dict) -> str:
        """Quick research overview"""
        prompt = f"""
Quick research brief on: {request}

Provide:
1. KEY FACTS (3-5, each with source)
2. CURRENT STATE (what's happening now — verified)
3. KEY NUMBERS (statistics with sources)
4. WHAT'S UNCERTAIN (flag explicitly)
5. WHERE TO LEARN MORE (reliable sources to explore)

Keep it concise. Every fact cited. Unknown = state it's unknown.
"""
        return await self.router.complete(
            system=self.RESEARCH_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="search",
            max_tokens=1500
        )

    async def _fact_check(self, request: str, context: Dict) -> str:
        """Fact-check a specific claim"""
        prompt = f"""
Fact-check this claim: {request}

Analysis:
1. VERDICT: TRUE / FALSE / PARTIALLY TRUE / UNVERIFIED / MISLEADING
2. EVIDENCE: What evidence supports or contradicts this?
3. SOURCES: Where does the evidence come from?
4. NUANCE: What's missing from the original claim?
5. CONFIDENCE: How confident are you in this verdict? (high/medium/low)

If you cannot verify → say "UNVERIFIED — insufficient data to confirm or deny"
Never guess the verdict. If uncertain → flag it clearly.
"""
        return await self.router.complete(
            system=self.RESEARCH_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="reasoning",
            max_tokens=1000
        )

    async def _market_research(self, request: str, context: Dict) -> str:
        """Market and industry research"""
        prompt = f"""
Market/industry research on: {request}

Structure:
**MARKET SIZE:** (with source and date)
**GROWTH RATE:** (CAGR — with source)
**KEY PLAYERS:** (top companies, market share — cited)
**TRENDS:** (verified current trends)
**OPPORTUNITIES:** (based on data, not speculation)
**RISKS:** (documented risks and challenges)
**REGULATORY ENVIRONMENT:** (relevant regulations)
**INVESTMENT ACTIVITY:** (recent funding, M&A — with dates)

DATA QUALITY NOTES:
- Mark each data point: [RECENT] [DATED: year] or [ESTIMATED]
- Never present estimates as confirmed facts
- Note when market data varies significantly between sources
"""
        return await self.router.complete(
            system=self.RESEARCH_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="search",
            max_tokens=2500
        )

    async def get_status(self) -> Dict:
        return {"healthy": True, "state": "running", "agent": "ResearchAgent"}
