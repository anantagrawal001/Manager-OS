"""
MANAGER OS — Conversation Agent (P1-11)
FILE: agents/conversation_agent.py
CREATED: 2026-05-31 | Claude Sonnet 4.6 — Phase B
PURPOSE: Handles memory queries — "what did I say about X last week?"
         Missing from codebase, referenced in final audit plan.
DO NOT DELETE — comment out with reason and date
"""

from typing import Dict, Any
from loguru import logger
from agents.base_agent import BaseAgent
from core.conversation_store import get_store


class ConversationAgent(BaseAgent):

    async def execute(self, request: str, context: Dict[str, Any]) -> str:
        store = get_store()
        req_lower = request.lower()

        if any(w in req_lower for w in ["recent", "last", "earlier"]):
            return await self._recent(store)
        elif any(w in req_lower for w in ["summarize", "summary"]):
            return await self._summarize(store)
        else:
            query = self._extract_topic(request)
            return await self._search(store, query)

    async def _recent(self, store) -> str:
        history = await store.get_history(limit=10)
        if not history:
            return "Sir, no conversation history yet — this is our first session."
        lines = []
        for e in history[-6:]:
            role = "Sir" if e["role"] == "user" else "Manager"
            ts = e.get("timestamp", "")[:16]
            content = e["content"][:120]
            lines.append(f"**{role}** [{ts}]: {content}{'...' if len(e['content']) > 120 else ''}")
        return "**Recent conversations, Sir:**\n\n" + "\n\n".join(lines)

    async def _search(self, store, query: str) -> str:
        results = await store.search(query, limit=5)
        if not results:
            return f"Sir, I couldn't find any past conversations about '{query}'."
        lines = []
        for r in results:
            role = "Sir" if r["role"] == "user" else "Manager"
            ts = r.get("timestamp", "")[:16]
            content = r["content"][:150]
            lines.append(f"**{role}** [{ts}]:\n{content}")
        return f"**Found {len(results)} conversation(s) about '{query}', Sir:**\n\n" + "\n\n---\n\n".join(lines)

    async def _summarize(self, store) -> str:
        history = await store.get_history(limit=20)
        if not history:
            return "Sir, no history to summarize yet."
        user_msgs = [e["content"][:80] for e in history if e["role"] == "user"]
        if self.router and user_msgs:
            try:
                summary = await self.router.complete(
                    system="Summarize these conversation topics in 3 bullet points. Be concise.",
                    messages=[{"role": "user", "content": "\n".join(user_msgs)}],
                    task_type="conversation", max_tokens=200
                )
                return f"**Conversation summary, Sir:**\n\n{summary}"
            except Exception:
                pass
        return "**Recent topics, Sir:**\n\n" + "\n".join(f"• {m}" for m in user_msgs[-5:])

    def _extract_topic(self, request: str) -> str:
        req = request.lower()
        for phrase in ["what did i say about", "when did i mention", "do you remember",
                       "tell me about", "find", "search for"]:
            req = req.replace(phrase, "").strip()
        return req.strip(" ?.,") or request

    async def get_status(self) -> Dict:
        return {"healthy": True, "state": "ready", "agent": "ConversationAgent"}
