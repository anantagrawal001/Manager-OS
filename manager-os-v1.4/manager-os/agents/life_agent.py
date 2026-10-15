"""
MANAGER OS — Life Agent
════════════════════════
FILE: agents/life_agent.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
PURPOSE: Personal life OS — daily planning, finance tracking, gold inventory,
         ETF management, expenses, reminders, health, education.

DO NOT DELETE ANY CODE — comment out with reason and date
"""

from typing import Dict, Any
from loguru import logger
from agents.base_agent import BaseAgent


class LifeAgent(BaseAgent):

    LIFE_SYSTEM = """
You are Anant's personal life manager. You help organize, track, and optimize
his daily life across all dimensions: finance, health, education, planning, and personal goals.
You're warm but direct. You remember context. You proactively flag things that matter.
"""

    # Superseded 2026-10-12: retained for rollback; corrected implementation below.
    # async def execute(self, request: str, context: Dict[str, Any]) -> str:
    #     req_lower = request.lower()
    #
    #     if any(w in req_lower for w in ["morning", "today", "briefing", "day"]):
    #         return await self._morning_briefing(request, context)
    #     elif any(w in req_lower for w in ["reminder", "schedule", "calendar", "task"]):
    #         return await self._planning(request, context)
    #     elif any(w in req_lower for w in ["expense", "budget", "spend", "money"]):
    #         return await self._finance_tracking(request, context)
    #     elif any(w in req_lower for w in ["learn", "study", "course", "education"]):
    #         return await self._learning_plan(request, context)
    #     else:
    #         return await self._ask_ai(request, system=self.LIFE_SYSTEM)

    def __init__(self, config, router, firewall):
        super().__init__(config, router, firewall)
        from core.local_tasks import LocalTasks
        self.tasks = LocalTasks(config.get('storage', {}).get('tasks_path', 'logs/tasks.db'))

    async def execute(self, request, context):
        import re
        from datetime import datetime, timedelta
        text = request.strip()
        match = re.search(r'\b(?:complete|finish|done) task\s+#?(\d+)\b', text, re.I)
        if match:
            found = self.tasks.complete(int(match[1]))
            return 'Sir, task completed.' if found else 'Sir, that open task was not found.'
        match = re.search(r'\badd task\s*:?\s*(.+)', text, re.I)
        if match:
            number = self.tasks.add(match[1])
            return f'Sir, saved task #{number}: {match[1]}'
        match = re.search(r'\bremind me (?:in (\d+) (seconds?|minutes?|hours?|days?) to (.+)|to (.+) in (\d+) (seconds?|minutes?|hours?|days?))$', text, re.I)
        if match:
            count, unit, title = (match[1], match[2], match[3]) if match[1] else (match[5], match[6], match[4])
            seconds = int(count) * {'second': 1, 'minute': 60, 'hour': 3600, 'day': 86400}[unit.lower().rstrip('s')]
            due = (datetime.now() + timedelta(seconds=seconds)).isoformat(timespec='seconds')
            number = self.tasks.add(title, due)
            return f'Sir, reminder #{number} saved for {due.replace("T", " ")}: {title}. Keep Manager OS running for the alert.'
        if re.search(r'\b(list tasks|show tasks|my tasks|morning|briefing|today)\b', text, re.I):
            tasks = self.tasks.list()
            if not tasks:
                return 'Sir, you have no open tasks. Say "add task" followed by your task.'
            return 'Your open tasks, Sir:\n' + '\n'.join(f"#{t['id']} {t['title']}" + (f" — due {t['due_at']}" if t['due_at'] else '') for t in tasks)
        if re.search(r'\b(remind|reminder|schedule|calendar)\b', text, re.I):
            return 'Sir, use "remind me in 10 minutes to take a break", or add a task and time in the Tasks panel. External calendars are not connected.'
        return await self._ask_ai(request, system=self.LIFE_SYSTEM + '\nNo finance, health or calendar accounts are connected. Do not claim to save or access them.')

    async def _morning_briefing(self, request: str, context: Dict) -> str:
        """Full morning briefing"""
        from datetime import datetime
        now = datetime.now()
        day = now.strftime("%A, %B %d")

        prompt = f"""
Generate a morning briefing for Sir. Today is {day}.

Cover exactly:
1. MARKET SNAPSHOT: NIFTY, SENSEX direction + key movers today
2. YOUR DAY: Any scheduled tasks or reminders I know about
3. WEATHER: General advice (hot/cold/rainy — dress accordingly)
4. ONE INSIGHT: One interesting thing worth knowing today (news, opportunity, idea)
5. HEALTH REMINDER: One simple wellness nudge

Keep it under 150 words total. Calm, composed, like a trusted advisor speaking.
End with: "What would you like to focus on first today, Sir?"
"""
        return await self.router.complete(
            system=self.LIFE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="conversation"
        )

    async def _planning(self, request: str, context: Dict) -> str:
        prompt = f"""
Help with planning/scheduling: {request}

Provide:
- Structured plan with time blocks
- Priority order (what matters most)
- Realistic time estimates
- Buffer time for unexpected things
- Any conflicts to be aware of
"""
        return await self._ask_ai(prompt, system=self.LIFE_SYSTEM)

    async def _finance_tracking(self, request: str, context: Dict) -> str:
        return await self._ask_ai(request, system=self.LIFE_SYSTEM)

    async def _learning_plan(self, request: str, context: Dict) -> str:
        prompt = f"""
Create a learning plan for: {request}

Include:
- Best free resources (courses, YouTube, docs)
- 30-day learning roadmap
- Daily time investment needed
- Milestones to track progress
- Projects to build while learning
"""
        return await self.router.complete(
            system=self.LIFE_SYSTEM,
            messages=[{"role": "user", "content": prompt}],
            task_type="conversation",
            max_tokens=2000
        )

    async def get_status(self) -> Dict:
        return {"healthy": True, "state": "running", "agent": "LifeAgent"}
