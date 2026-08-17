"""FACTRON application composition root."""

from __future__ import annotations

from dataclasses import dataclass

from agent.executor import ExecutionContext, StepExecutor
from agent.loop import AgentLoop
from agent.planner import DeterministicPlanner
from .api import FactronAPI


def _validate_task(
    context: ExecutionContext,
    arguments: dict[str, object],
) -> dict[str, object]:
    """Validate and normalize a task at the execution boundary."""
    task = arguments.get("task")

    if not isinstance(task, str) or not task.strip():
        raise ValueError("A non-empty task is required.")

    normalized = " ".join(task.split())

    context.state["validated_task"] = normalized

    return {
        "accepted": True,
        "task": normalized,
        "run_id": context.run_id,
    }


@dataclass(slots=True)
class FactronApplication:
    """Fully composed FACTRON runtime."""

    api: FactronAPI

    def health(self):
        """Expose application health."""
        return self.api.health()

    def execute(self, task: str, run_id: str) -> dict[str, object]:
        """Execute a task through the application boundary."""
        from .api import TaskRequest

        request = TaskRequest(
            task=task,
            run_id=run_id,
        )

        return self.api.execute_task(request).to_dict()


def create_application() -> FactronApplication:
    """Construct a validated FACTRON application instance."""
    planner = DeterministicPlanner()
    executor = StepExecutor()

    executor.register(
        "factron.validate_task",
        _validate_task,
    )

    agent_loop = AgentLoop(
        planner=planner,
        executor=executor,
        max_steps=32,
    )

    return FactronApplication(
        api=FactronAPI(agent_loop),
    )
