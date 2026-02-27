"""Planner converts intent into a DAG execution plan.

Takes structured intent from IntentClassifier and builds a Plan
with nodes and dependencies.
"""
from app.orchestrator.dag import Plan, PlanNode


class QueryPlanner:
    """Convert intent classification into an execution plan."""

    def build_plan(self, intent: dict) -> Plan:
        plan = Plan()
        steps = intent.get("steps", [])

        # Attach intent metadata to plan (useful later)
        plan.intent = intent

        if not steps:
            return plan

        # First node
        plan.add_node(PlanNode(id=steps[0], dependencies=[]))

        # Sequential dependency chain
        for i in range(1, len(steps)):
            plan.add_node(
                PlanNode(
                    id=steps[i],
                    dependencies=[steps[i - 1]],
                )
            )

        plan.validate()
        return plan