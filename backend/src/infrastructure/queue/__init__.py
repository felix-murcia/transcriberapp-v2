"""Infrastructure layer - job queue implementations.
Concrete implementations of background job queue ports.
"""
from fastapi import BackgroundTasks
from backend.src.domain.ports import JobQueuePort


class FastAPIBackgroundTasksAdapter(JobQueuePort):
    """Adapter for FastAPI BackgroundTasks as a job queue."""

    def __init__(self, background_tasks: BackgroundTasks = None):
        self._background_tasks = background_tasks

    def set_background_tasks(self, background_tasks: BackgroundTasks) -> None:
        """Set the background tasks instance (for dependency injection)."""
        self._background_tasks = background_tasks

    def add_task(self, func, *args, **kwargs) -> None:
        """Add a task to the background queue."""
        if self._background_tasks is None:
            raise RuntimeError("BackgroundTasks not set. Call set_background_tasks() first.")
        self._background_tasks.add_task(func, *args, **kwargs)
