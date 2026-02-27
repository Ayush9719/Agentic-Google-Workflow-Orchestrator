"""Execution engine for orchestration plans.

Executes a DAG sequentially by resolving dependencies.
Dispatches to service agents and tracks results.
"""
from typing import Any
import asyncio
from app.orchestrator.dag import Plan, PlanNode
from app.agents.gmail import GmailAgent
from app.agents.gcal import GCalAgent


class OrchestratorEngine:
    """Execute a Plan (DAG) by resolving dependencies and running steps."""

    # Mapping of step_id to service
    STEP_TO_SERVICE = {
        "search_gmail_for_booking": "gmail",
        "draft_cancellation_email": "gmail",
        "find_calendar_event": "gcal",
    }

    def __init__(self):
        self.gmail_agent = GmailAgent()
        self.gcal_agent = GCalAgent()

    def _resolve_service(self, step_id: str) -> str:
        """Resolve which service handles a step.

        Args:
            step_id: Step identifier

        Returns:
            Service name (e.g., "gmail", "gcal", "gdrive") or "unknown"
        """
        return self.STEP_TO_SERVICE.get(step_id, "unknown")

    async def execute(self, plan: Plan, context: dict) -> dict:
        """Execute all nodes in a plan.

        Args:
            plan: Plan (DAG) to execute
            context: Execution context (optional state/data)

        Returns:
            Dict mapping step_id -> result
        """
        completed: set[str] = set()
        results: dict[str, Any] = {}

        context = context or {}
        context["user_id"] = context.get("user_id")
        context["intent"] = getattr(plan, "intent", {})

        while len(completed) < len(plan.nodes):
            ready_nodes = plan.get_ready_nodes(completed)

            if not ready_nodes:
                raise RuntimeError("Circular dependency or missing nodes")

            tasks = [
                self._execute_step(node.id, context)
                for node in ready_nodes
            ]

            batch_results = await asyncio.gather(*tasks)

            for node, result in zip(ready_nodes, batch_results):
                node.result = result
                results[node.id] = result
                completed.add(node.id)
                context[node.id] = result

        return results

    async def _execute_step(self, step_id: str, context: dict) -> dict:
        """Execute a single step and return result.

        Args:
            step_id: Node ID (step name)
            context: Execution context

        Returns:
            Result dict
        """
        # Resolve which service handles this step
        service = self._resolve_service(step_id)

        if service == "gmail":
            return await self.gmail_agent.handle(step_id, context)
        elif service == "gcal":
            return await self.gcal_agent.handle(step_id, context)
        elif step_id == "send_email":
            return await self._send_email(context)
        else:
            # Unknown step: return empty result
            return {"status": "unknown_step", "step_id": step_id}

    async def _send_email(self, context: dict) -> dict:
        """Mock: send email."""
        return {
            "status": "completed",
            "step": "send_email",
            "sent_to": "support@airline.com"
        }
