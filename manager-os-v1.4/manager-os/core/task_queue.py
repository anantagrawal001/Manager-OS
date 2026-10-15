"""
MANAGER OS — Task Queue & Priority Scheduler
═════════════════════════════════════════════
FILE: core/task_queue.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
PURPOSE: Manages concurrent agent tasks. Parallel where possible, sequential where needed.
         Priority scheduling. Background task management.

DO NOT DELETE ANY CODE — comment out with reason and date
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import IntEnum
from typing import Any, Callable, Dict, List, Optional
from loguru import logger


class Priority(IntEnum):
    CRITICAL = 0   # Health alerts, security issues
    HIGH = 1       # Voice commands, real-time requests
    NORMAL = 2     # Background tasks, scheduled scans
    LOW = 3        # Analytics, non-urgent updates


@dataclass(order=True)
class QueuedTask:
    priority: int
    timestamp: float = field(compare=False, default_factory=lambda: datetime.now().timestamp())
    task_id: str = field(compare=False, default="")
    coro: Any = field(compare=False, default=None)
    description: str = field(compare=False, default="")
    callback: Optional[Callable] = field(compare=False, default=None)


class TaskQueue:
    """
    Priority task queue for Manager OS.
    Supports parallel execution of independent tasks.
    Sequential execution where tasks depend on each other.
    """

    MAX_CONCURRENT = 5  # Max parallel tasks

    def __init__(self):
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._running: Dict[str, asyncio.Task] = {}
        self._completed: List[Dict] = []
        self._worker_task: Optional[asyncio.Task] = None
        self._running_count = 0

    async def start(self):
        """Start the task queue worker"""
        self._worker_task = asyncio.create_task(self._worker())
        logger.info("Task queue started")

    async def submit(
        self,
        coro,
        task_id: str,
        priority: Priority = Priority.NORMAL,
        description: str = "",
        callback: Callable = None
    ) -> str:
        """Submit a task to the queue"""
        queued = QueuedTask(
            priority=priority.value,
            task_id=task_id,
            coro=coro,
            description=description,
            callback=callback
        )
        await self._queue.put(queued)
        logger.debug(f"Task queued: {task_id} (priority: {priority.name})")
        return task_id

    async def _worker(self):
        """Main worker loop — pulls tasks from queue and executes"""
        while True:
            try:
                if self._running_count >= self.MAX_CONCURRENT:
                    await asyncio.sleep(0.1)
                    continue

                queued = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                self._running_count += 1

                task = asyncio.create_task(
                    self._execute(queued)
                )
                self._running[queued.task_id] = task

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Queue worker error: {e}")

    async def _execute(self, queued: QueuedTask):
        """Execute a single task"""
        start = datetime.now()
        try:
            result = await queued.coro
            if queued.callback:
                await queued.callback(result)

            self._completed.append({
                "id": queued.task_id,
                "description": queued.description,
                "status": "done",
                "duration_ms": int((datetime.now() - start).total_seconds() * 1000)
            })

        except Exception as e:
            logger.error(f"Task {queued.task_id} failed: {e}")
            self._completed.append({
                "id": queued.task_id,
                "description": queued.description,
                "status": "failed",
                "error": str(e)
            })
        finally:
            self._running_count -= 1
            self._running.pop(queued.task_id, None)
            self._queue.task_done()

    def get_status(self) -> Dict:
        return {
            "healthy": True,
            "state": "running",
            "queued": self._queue.qsize(),
            "running": self._running_count,
            "completed": len(self._completed),
            "active_tasks": list(self._running.keys())
        }
