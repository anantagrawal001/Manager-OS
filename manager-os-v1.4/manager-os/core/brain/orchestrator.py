"""
MANAGER OS — Brain: Orchestrator
══════════════════════════════════
FILE: core/brain/orchestrator.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
PURPOSE: Stage 3 of brain pipeline. Takes TaskPlan and executes it.
         Runs parallel tasks with asyncio. Sequential tasks in order.
         Each subtask routed to correct domain plugin.

DO NOT DELETE ANY CODE — comment out with reason and date
"""

import asyncio
from typing import Dict, Any, Optional
from loguru import logger

from core.brain.planner import TaskPlan, SubTask


class Orchestrator:
    """
    Executes task plans from Planner.
    Parallel where deps allow. Sequential where required.
    """

    def __init__(self, agents: Dict):
        self.agents = agents

    async def execute(self, plan: TaskPlan, context: Dict) -> Dict[str, Any]:
        """
        Execute a task plan.
        Returns dict of {task_id: result} for all completed tasks.
        """
        results: Dict[str, Any] = {}
        max_iterations = 20  # Safety — prevent infinite loop

        for iteration in range(max_iterations):
            if plan.is_complete():
                break

            # Get tasks ready to run (deps satisfied)
            ready = plan.get_ready_tasks()
            if not ready:
                # Waiting on deps — check for stuck state
                logger.warning(f"No tasks ready at iteration {iteration} — possible dep cycle")
                break

            # Run all ready tasks in parallel
            if len(ready) == 1:
                # Single task — run directly
                result = await self._execute_subtask(ready[0], results, context)
                results[ready[0].id] = result
                ready[0].result = result
                ready[0].status = "done"
            else:
                # Multiple tasks — run in parallel
                tasks = [
                    self._execute_subtask(subtask, results, context)
                    for subtask in ready
                ]
                parallel_results = await asyncio.gather(*tasks, return_exceptions=True)

                for subtask, result in zip(ready, parallel_results):
                    if isinstance(result, Exception):
                        logger.error(f"Subtask {subtask.id} failed: {result}")
                        subtask.status = "failed"
                        results[subtask.id] = f"Error: {result}"
                    else:
                        subtask.result = result
                        subtask.status = "done"
                        results[subtask.id] = result

        return results

    async def _execute_subtask(
        self,
        subtask: SubTask,
        prior_results: Dict[str, Any],
        context: Dict
    ) -> str:
        """Execute a single subtask via the appropriate agent"""
        logger.debug(f"Executing subtask: {subtask.id} → {subtask.domain}")

        # Build context for this subtask (include results from deps)
        subtask_context = {
            **context,
            "prior_results": {
                dep: prior_results.get(dep, "")
                for dep in subtask.depends_on
            }
        }

        # Route to agent
        agent = self.agents.get(subtask.domain)
        if not agent:
            # Try manager conversation fallback
            logger.warning(f"No agent for domain: {subtask.domain} — using conversation")
            return f"Processed: {subtask.description}"

        try:
            result = await asyncio.wait_for(
                agent.execute(subtask.description, subtask_context),
                timeout=120.0  # 2 minute timeout per subtask
            )
            return result

        except asyncio.TimeoutError:
            logger.error(f"Subtask {subtask.id} timed out")
            return f"Task timed out: {subtask.description}"
        except Exception as e:
            logger.error(f"Subtask {subtask.id} error: {e}")
            return f"Error in {subtask.description}: {str(e)}"

    def compile_results(self, plan: TaskPlan, results: Dict[str, Any]) -> str:
        """Compile all subtask results into a coherent response"""
        if len(results) == 1:
            # Single task — return result directly
            return list(results.values())[0]

        # Multiple results — join with context
        parts = []
        for subtask in plan.subtasks:
            result = results.get(subtask.id, "")
            if result:
                parts.append(f"**{subtask.description}:**\n{result}")

        return "\n\n".join(parts)
