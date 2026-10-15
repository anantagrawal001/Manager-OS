"""
MANAGER OS — Brain: Planner
════════════════════════════
FILE: core/brain/planner.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
PURPOSE: Stage 2 of brain pipeline. Takes parsed intent and breaks it into
         the smallest independent subtasks. Identifies parallel vs sequential.
         Example: "prep me for Google interview" → 5 parallel + 2 sequential subtasks

DO NOT DELETE ANY CODE — comment out with reason and date
"""

import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class SubTask:
    id: str
    description: str
    domain: str                      # Which agent handles this
    depends_on: List[str] = field(default_factory=list)  # IDs of subtasks that must complete first
    inputs: Dict[str, Any] = field(default_factory=dict)
    priority: int = 2
    estimated_seconds: int = 10
    status: str = "pending"
    result: Optional[Any] = None


@dataclass
class TaskPlan:
    original_request: str
    intent: str
    subtasks: List[SubTask]
    total_estimated_seconds: int = 0

    def get_ready_tasks(self) -> List[SubTask]:
        """Get subtasks whose dependencies are all completed"""
        completed_ids = {t.id for t in self.subtasks if t.status == "done"}
        return [
            t for t in self.subtasks
            if t.status == "pending"
            and all(dep in completed_ids for dep in t.depends_on)
        ]

    def is_complete(self) -> bool:
        return all(t.status in ("done", "failed") for t in self.subtasks)


class Planner:
    """
    Breaks complex requests into executable subtask plans.
    Identifies parallel vs sequential dependencies.
    """

    # Known multi-step patterns
    COMPLEX_PATTERNS = {
        "interview": ["research_company", "pull_resume", "identify_role_requirements",
                      "generate_questions", "create_model_answers", "schedule_mock"],
        "apply_job": ["find_job_description", "tailor_resume", "write_cover_letter",
                      "find_recruiter_email", "send_cold_email"],
        "morning_briefing": ["market_conditions", "check_emails", "check_messages",
                             "portfolio_performance", "job_updates", "health_log"],
        "grow_instagram": ["analyze_current_performance", "identify_content_gaps",
                           "create_content_calendar", "generate_content", "schedule_posts"],
        "trade_stock": ["technical_analysis", "sentiment_analysis", "fundamental_check",
                        "risk_assessment", "consensus_vote", "execute_if_approved"],
    }

    def __init__(self, router):
        self.router = router

    async def plan(self, user_input: str, intent: str, context: Dict) -> TaskPlan:
        """
        Create execution plan for a request.
        Simple requests → single subtask.
        Complex requests → AI-generated multi-step plan.
        """
        # Check if matches a known complex pattern
        for pattern_key, pattern_steps in self.COMPLEX_PATTERNS.items():
            if pattern_key in user_input.lower() or pattern_key in intent.lower():
                return self._build_pattern_plan(user_input, intent, pattern_key, pattern_steps)

        # For complex/multi-part requests — use AI to generate plan
        if self._is_complex_request(user_input):
            return await self._ai_generated_plan(user_input, intent, context)

        # Simple request — single subtask
        return TaskPlan(
            original_request=user_input,
            intent=intent,
            subtasks=[
                SubTask(
                    id="task_1",
                    description=user_input,
                    domain=intent,
                    estimated_seconds=10
                )
            ],
            total_estimated_seconds=10
        )

    def _is_complex_request(self, user_input: str) -> bool:
        """Detect if request needs multi-step planning"""
        complexity_indicators = [
            " and ", " then ", " after ", " also ",
            "prepare", "analyze", "research and", "find and",
            "create and send", "build and deploy"
        ]
        lower = user_input.lower()
        return any(indicator in lower for indicator in complexity_indicators)

    def _build_pattern_plan(
        self, request: str, intent: str, pattern: str, steps: List[str]
    ) -> TaskPlan:
        """Build plan from known pattern"""
        subtasks = []
        prev_id = None

        for i, step in enumerate(steps):
            task_id = f"{pattern}_{i+1}"
            subtask = SubTask(
                id=task_id,
                description=step.replace("_", " ").title(),
                domain=intent,
                depends_on=[prev_id] if prev_id and i > 2 else [],  # First 3 can be parallel
                estimated_seconds=15
            )
            subtasks.append(subtask)
            prev_id = task_id

        return TaskPlan(
            original_request=request,
            intent=intent,
            subtasks=subtasks,
            total_estimated_seconds=len(steps) * 15
        )

    async def _ai_generated_plan(self, request: str, intent: str, context: Dict) -> TaskPlan:
        """Use AI to generate a custom task plan"""
        prompt = f"""
Break this request into specific subtasks for execution.

Request: {request}
Domain: {intent}

Return JSON only:
{{
  "subtasks": [
    {{
      "id": "task_1",
      "description": "What to do",
      "domain": "which agent (trading/career/social/life/creative/communication/builder/files/growth)",
      "depends_on": [],
      "estimated_seconds": 10
    }}
  ]
}}

Rules:
- Independent tasks have empty depends_on (run in parallel)
- Sequential tasks list IDs they depend on
- Keep subtasks atomic and specific
- Maximum 8 subtasks
"""
        try:
            response = await self.router.complete(
                system="You are a task planner. Return only valid JSON.",
                messages=[{"role": "user", "content": prompt}],
                task_type="reasoning"
            )

            # Parse JSON
            response = response.strip()
            if response.startswith("```"):
                response = response.split("```")[1]
                if response.startswith("json"):
                    response = response[4:]

            plan_data = json.loads(response)
            subtasks = [
                SubTask(**task) for task in plan_data.get("subtasks", [])
            ]

            return TaskPlan(
                original_request=request,
                intent=intent,
                subtasks=subtasks,
                total_estimated_seconds=sum(t.estimated_seconds for t in subtasks)
            )

        except Exception as e:
            logger.error(f"AI planning failed: {e} — falling back to single task")
            return TaskPlan(
                original_request=request,
                intent=intent,
                subtasks=[SubTask(id="task_1", description=request, domain=intent)],
                total_estimated_seconds=15
            )
