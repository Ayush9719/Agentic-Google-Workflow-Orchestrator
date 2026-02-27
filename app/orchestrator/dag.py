"""DAG representation for execution planning.

Defines the structure of a plan with dependencies.
Does not execute; only tracks which steps can run next.
"""
from typing import Any


class PlanNode:
    """A single step in the execution plan."""

    def __init__(self, id: str, dependencies: list[str] | None = None):
        self.id = id
        self.dependencies = dependencies or []
        self.result = None

    def __repr__(self):
        return f"PlanNode(id={self.id}, deps={self.dependencies}, result={self.result})"


class Plan:
    """Execution plan with dependency tracking."""

    def __init__(self):
        self.nodes: dict[str, PlanNode] = {}

    def add_node(self, node: PlanNode) -> None:
        if node.id in self.nodes:
            raise ValueError(f"Node '{node.id}' already exists in plan")
        self.nodes[node.id] = node

    def validate(self) -> None:
        """Ensure all dependencies reference valid nodes."""
        for node in self.nodes.values():
            for dep in node.dependencies:
                if dep not in self.nodes:
                    raise ValueError(
                        f"Node '{node.id}' depends on unknown node '{dep}'"
                    )

    def get_ready_nodes(self, completed_ids: set[str]) -> list[PlanNode]:
        ready = []
        for node_id, node in self.nodes.items():
            if node_id not in completed_ids:
                if all(dep in completed_ids for dep in node.dependencies):
                    ready.append(node)
        return ready

    def __repr__(self):
        return f"Plan(nodes={list(self.nodes.keys())})"