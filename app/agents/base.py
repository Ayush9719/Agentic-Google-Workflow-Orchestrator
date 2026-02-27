"""Base agent interface.

All agents inherit from BaseAgent and implement the handle method.
This allows the orchestrator engine to dispatch work uniformly.
"""
from abc import ABC, abstractmethod


class BaseAgent(ABC):
    """Abstract base class for all service agents.
    
    Agents handle specific steps in an orchestration plan.
    """

    @abstractmethod
    async def handle(self, step_id: str, context: dict) -> dict:
        """Execute a step and return result.

        Args:
            step_id: The step identifier (e.g., "search_gmail_for_booking")
            context: Execution context with state and data

        Returns:
            Result dict with step output
        """
        pass
