"""Placeholder for a task queue adapter (e.g., Celery, RQ, or a lightweight in-process queue).
Keep interface small: enqueue(task), worker loop, status.
"""
from typing import Callable, Any


class TaskQueue:
    def __init__(self):
        self._tasks = []

    def enqueue(self, func: Callable[..., Any], *args, **kwargs):
        self._tasks.append((func, args, kwargs))

    def run_all(self):
        results = []
        while self._tasks:
            func, args, kwargs = self._tasks.pop(0)
            results.append(func(*args, **kwargs))
        return results
