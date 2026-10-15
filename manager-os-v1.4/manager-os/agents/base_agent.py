"""
MANAGER OS — Base Agent
════════════════════════
FILE: agents/base_agent.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
PURPOSE: Base class for all domain agents. Defines interface.
         All agents inherit from this and implement execute().

DO NOT DELETE ANY CODE — comment out with reason and date
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from loguru import logger


class BaseAgent(ABC):
    """
    Base class for all Manager OS domain agents.
    
    Every agent must:
    1. Inherit from BaseAgent
    2. Implement execute(request, context) -> str
    3. Implement get_status() -> dict
    4. Register in plugin_manager.py
    """

    def __init__(self, config: dict, router, firewall):
        self.config = config
        self.router = router
        self.firewall = firewall
        self.name = self.__class__.__name__
        self._healthy = True
        self._initialized = False

    async def initialize(self):
        """Called on startup — override for agent-specific init"""
        self._initialized = True
        logger.info(f"Agent initialized: {self.name}")

    @abstractmethod
    async def execute(self, request: str, context: Dict[str, Any]) -> str:
        """
        Main execution method.
        
        Args:
            request: What Anant (Sir) wants done
            context: Prior results, conversation history, session data
            
        Returns:
            Result string — will be polished by Manager before Anant sees it
        """
        pass

    async def get_status(self) -> Dict:
        """Return agent health status"""
        return {
            "healthy": self._healthy,
            "state": "running" if self._healthy else "failed",
            "initialized": self._initialized,
            "agent": self.name
        }

    async def restart(self):
        """Attempt restart — called by Health Agent"""
        logger.info(f"Restarting agent: {self.name}")
        self._healthy = True
        await self.initialize()

    def _sanitize_for_api(self, data: str) -> str:
        """
        Sanitize data before sending to external AI APIs.
        Removes or replaces personally identifiable information.
        Uses firewall.sanitize() for full processing.
        """
        if self.firewall:
            return self.firewall.sanitize(data)
        return data

    async def _ask_ai(
        self,
        prompt: str,
        system: str = "",
        task_type: str = "conversation"
    ) -> str:
        """Convenience method — ask AI model via router"""
        return await self.router.complete(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            task_type=task_type
        )
