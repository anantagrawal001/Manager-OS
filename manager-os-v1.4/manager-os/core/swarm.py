"""
MANAGER OS — Swarm Intelligence Engine
FILE: core/swarm.py
CREATED: 2026-05-31 | Claude Sonnet 4.6
PURPOSE: Ruflo/Claude-Flow inspired multi-agent swarm coordination.
         Queen (Manager) routes to specialized Worker agents.
         For complex tasks: workers debate → consensus → execute.
         Hook system: learned routing patterns from past interactions.

INSPIRED BY: ruvnet/ruflo — 7-layer architecture, Queen-led swarms,
             hook system, SPARC methodology, ReasoningBank patterns.

DO NOT DELETE ANY CODE — comment out with reason and date
"""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class SwarmTask:
    id: str
    request: str
    intent: str
    assigned_agents: List[str] = field(default_factory=list)
    results: Dict[str, str] = field(default_factory=dict)
    consensus: Optional[str] = None
    status: str = "pending"  # pending | running | consensus | done | failed
    created: float = field(default_factory=time.time)
    require_consensus: bool = False
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Hook:
    """Learned routing pattern — fires when conditions match"""
    name: str
    trigger_keywords: List[str]
    target_agent: str
    confidence: float = 0.8
    fire_count: int = 0
    last_fired: Optional[float] = None
    enabled: bool = True


class SwarmEngine:
    """
    Queen-led swarm intelligence.
    Routes tasks to best agents, enables multi-agent consensus for critical decisions.
    Learns routing patterns over time via hook system.

    Inspired by ruvnet/ruflo architecture but simplified for Manager OS:
    - No IPFS marketplace (local skills only)
    - No HNSW vector indexing (ChromaDB for semantic, SQLite for structured)
    - Hooks = learned routing patterns stored in hooks.json
    """

    HOOKS_FILE = Path("./skills/hooks.json")
    PATTERNS_FILE = Path("./skills/patterns.json")

    # Tasks requiring multi-agent consensus (high stakes)
    CONSENSUS_TASKS = {
        "trading": ["trading", "files", "research"],      # Trading: technical + research + risk
        "legal": ["research", "communication", "builder"],
        "financial": ["life", "trading", "research"],
    }

    def __init__(self, config: dict, agents: Dict[str, Any] = None, router=None):
        self.config = config
        self.agents = agents or {}
        self.router = router
        self.hooks: List[Hook] = []
        self.active_tasks: Dict[str, SwarmTask] = {}
        self.completed_tasks: List[SwarmTask] = []
        self._load_hooks()
        logger.info(f"SwarmEngine initialized — {len(self.hooks)} hooks loaded")

    def _load_hooks(self):
        """Load learned routing hooks from disk"""
        self.HOOKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if self.HOOKS_FILE.exists():
            try:
                data = json.loads(self.HOOKS_FILE.read_text())
                self.hooks = [Hook(**h) for h in data]
            except Exception:
                self.hooks = []
        self._ensure_default_hooks()

    def _ensure_default_hooks(self):
        """Seed default routing hooks"""
        defaults = [
            Hook("trade_signals",      ["buy", "sell", "trade", "stock", "market", "nifty", "sensex"],    "trading",       0.9),
            Hook("career_actions",     ["resume", "job", "apply", "interview", "cv", "linkedin"],         "career",        0.9),
            Hook("build_code",         ["build", "code", "create app", "program", "script", "deploy"],    "builder",       0.85),
            Hook("social_content",     ["instagram", "post", "reel", "caption", "content", "viral"],      "social",        0.85),
            Hook("research_deep",      ["research", "thesis", "investigate", "analyze", "deep dive"],     "research",      0.85),
            Hook("file_operations",    ["find file", "search file", "send file", "download", "locate"],   "files",         0.9),
            Hook("morning_briefing",   ["morning", "briefing", "today's plan", "what's today"],           "life",          0.9),
            Hook("creative_work",      ["image", "design", "poster", "logo", "visual", "generate image"], "creative",      0.8),
            Hook("self_heal_check",    ["what did you fix", "system status", "health check", "errors"],   "self_heal",     0.95),
            Hook("api_discovery",      ["new model", "free api", "nvidia nim", "groq", "which models"],   "api_scout",     0.9),
        ]
        existing_names = {h.name for h in self.hooks}
        for d in defaults:
            if d.name not in existing_names:
                self.hooks.append(d)

    def _save_hooks(self):
        try:
            data = [
                {"name": h.name, "trigger_keywords": h.trigger_keywords,
                 "target_agent": h.target_agent, "confidence": h.confidence,
                 "fire_count": h.fire_count, "last_fired": h.last_fired,
                 "enabled": h.enabled}
                for h in self.hooks
            ]
            self.HOOKS_FILE.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Hook save error: {e}")

    def match_hook(self, request: str) -> Optional[str]:
        """Find best matching hook for a request"""
        req_lower = request.lower()
        best_hook = None
        best_score = 0.0

        for hook in self.hooks:
            if not hook.enabled:
                continue
            matches = sum(1 for kw in hook.trigger_keywords if kw in req_lower)
            if matches == 0:
                continue
            score = (matches / len(hook.trigger_keywords)) * hook.confidence
            if score > best_score:
                best_score = score
                best_hook = hook

        if best_hook and best_score > 0.3:
            best_hook.fire_count += 1
            best_hook.last_fired = time.time()
            logger.debug(f"Hook fired: {best_hook.name} → {best_hook.target_agent} (score: {best_score:.2f})")
            return best_hook.target_agent

        return None

    def learn_routing(self, request: str, agent_used: str, success: bool):
        """Learn from successful routing decisions"""
        if not success:
            return

        # Find words that might be good triggers
        words = [w.lower() for w in request.split() if len(w) > 3]

        # Check if any existing hook covers this
        for hook in self.hooks:
            if hook.target_agent == agent_used:
                # Boost confidence for successful patterns
                hook.confidence = min(0.98, hook.confidence + 0.01)
                break

        self._save_hooks()

    async def dispatch(self, request: str, intent: str, context: Dict[str, Any] = None) -> str:
        """
        Main dispatch method — routes to best agent(s).
        For consensus-required tasks: multiple agents run in parallel.
        """
        task = SwarmTask(
            id=f"swarm_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            request=request,
            intent=intent,
            context=context or {},
            # Old consensus invoked unrelated action agents and could duplicate side effects.
            require_consensus=False,
        )
        self.active_tasks[task.id] = task

        try:
            if task.require_consensus:
                result = await self._consensus_dispatch(task)
            else:
                result = await self._single_dispatch(task)

            task.status = "done"
            task.consensus = result
            self.completed_tasks.append(task)
            if len(self.completed_tasks) > 100:
                self.completed_tasks = self.completed_tasks[-100:]
            return result

        except Exception as e:
            task.status = "failed"
            logger.error(f"Swarm dispatch failed: {e}")
            return f"Sir, the swarm dispatch failed: {str(e)[:80]}"
        finally:
            self.active_tasks.pop(task.id, None)

    # Superseded 2026-10-12: retained for rollback; corrected implementation below.
    # async def _single_dispatch(self, task: SwarmTask) -> str:
    #     """Route to best single agent"""
    #     # First check hooks
    #     agent_name = self.match_hook(task.request)
    #
    #     # Fall back to intent-based routing
    #     if not agent_name:
    #         agent_name = task.intent if task.intent in self.agents else None
    #
    #     if agent_name and agent_name in self.agents:
    #         task.assigned_agents = [agent_name]
    #         task.status = "running"
    #         try:
    #             result = await self.agents[agent_name].execute(task.request, task.context)
    #             self.learn_routing(task.request, agent_name, bool(result))
    #             return result or f"Sir, the {agent_name} agent returned an empty result."
    #         except Exception as e:
    #             logger.warning(f"Agent {agent_name} failed: {e}")
    #
    #     # No agent matched — use router directly
    #     if self.router:
    #         return await self.router.complete(
    #             system=self.router.MANAGER_SYSTEM_PROMPT,
    #             messages=[{"role": "user", "content": task.request}],
    #             task_type="conversation"
    #         )
    #     return "Sir, no agent or router available for this request."

    async def _single_dispatch(self, task):
        # The explicit classifier wins. Hooks must not redirect a concrete action.
        name = task.intent if task.intent in self.agents else self.match_hook(task.request)
        if not name or name not in self.agents:
            return 'Sir, no executable agent is registered for this command.'
        task.assigned_agents = [name]
        task.status = 'running'
        return await self.agents[name].execute(task.request, task.context)

    async def _consensus_dispatch(self, task: SwarmTask) -> str:
        """
        Multi-agent consensus for high-stakes tasks.
        Multiple agents analyze in parallel → combine insights → return consensus.
        Used for: trading decisions, financial planning, legal analysis.
        """
        agent_names = self.CONSENSUS_TASKS.get(task.intent, [task.intent])
        available = [n for n in agent_names if n in self.agents]

        if not available:
            return await self._single_dispatch(task)

        task.assigned_agents = available
        task.status = "consensus"
        logger.info(f"Consensus dispatch: {task.id} → {available}")

        # Run all agents in parallel
        futures = []
        for name in available:
            futures.append(self._safe_agent_call(name, task.request, task.context))

        results = await asyncio.gather(*futures, return_exceptions=True)

        # Collect valid results
        valid = {}
        for name, result in zip(available, results):
            if isinstance(result, str) and result:
                valid[name] = result
                task.results[name] = result

        if not valid:
            return await self._single_dispatch(task)

        if len(valid) == 1:
            return list(valid.values())[0]

        # Synthesize consensus
        synthesis_prompt = (
            f"Sir asked: '{task.request}'\n\n"
            f"Multiple agent analyses:\n\n"
        )
        for agent, analysis in valid.items():
            synthesis_prompt += f"**{agent.upper()} Agent:**\n{analysis[:400]}\n\n"
        synthesis_prompt += (
            "Synthesize these into a single cohesive response. "
            "Address Sir directly, highlight key consensus points and any disagreements. "
            "Be decisive — give a clear recommendation."
        )

        if self.router:
            return await self.router.complete(
                system=self.router.MANAGER_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": synthesis_prompt}],
                task_type="reasoning"
            )
        return "\n\n".join(f"**{k}:** {v}" for k, v in valid.items())

    async def _safe_agent_call(self, name: str, request: str, context: Dict) -> Optional[str]:
        try:
            return await asyncio.wait_for(
                self.agents[name].execute(request, context),
                timeout=30.0
            )
        except Exception as e:
            logger.warning(f"Consensus agent {name} failed: {e}")
            return None

    def get_status(self) -> Dict:
        return {
            "hooks": len(self.hooks),
            "active_tasks": len(self.active_tasks),
            "completed_tasks": len(self.completed_tasks),
            "agents_registered": len(self.agents),
            "healthy": True,
        }

    def add_hook(self, name: str, keywords: List[str], agent: str, confidence: float = 0.8):
        """Sir can add custom routing hooks at runtime"""
        self.hooks = [h for h in self.hooks if h.name != name]  # Replace if exists
        self.hooks.append(Hook(name=name, trigger_keywords=keywords,
                               target_agent=agent, confidence=confidence))
        self._save_hooks()
        logger.info(f"Hook added: {name} → {agent}")
