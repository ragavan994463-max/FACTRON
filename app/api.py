"""FACTRON application API contracts.

This module provides a framework-independent API boundary. A web framework
can be attached later without changing the underlying FACTRON architecture.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from agent.executor import StepExecutor
from agent.loop import AgentLoop, AgentRunResult
from agent.planner import DeterministicPlanner


@dataclass(frozen=True, slots=True)
class HealthResponse:
    """Machine-readable application health response."""

    status: str
    service: str
    version: str


@dataclass(frozen=True, slots=True)
class TaskRequest:
    """Validated request submitted to FACTRON."""

    task: str
    run_id: str
    context: Mapping[str, Any] | None = None

    def __post_init__(self) -> None:
        if not self.task.strip():
            raise ValueError("task cannot be empty.")
        if not self.run_id.strip():
            raise ValueError("run_id cannot be empty.")


@dataclass(frozen=True, slots=True)
class TaskResponse:
    """Stable external representation of an agent result."""

    run_id: str
    status: str
    outputs: tuple[Any, ...]
    errors: tuple[str, ...]
    completed_steps: int
    failed_steps: int

    @classmethod
    def from_result(cls, result: AgentRunResult) -> "TaskResponse":
        """Convert an internal agent result to an API response."""
        return cls(
            run_id=result.run_id,
            status=result.status.value,
            outputs=result.outputs,
            errors=result.errors,
            completed_steps=result.completed_steps,
            failed_steps=result.failed_steps,
        )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible representation."""
        return asdict(self)


class FactronAPI:
    """Application-facing service boundary.

    The API delegates execution to the agent layer and deliberately contains
    no model-provider or storage implementation details.
    """

    def __init__(self, agent_loop: AgentLoop) -> None:
        self._agent_loop = agent_loop

    def health(self) -> HealthResponse:
        """Return FACTRON service health."""
        return HealthResponse(
            status="healthy",
            service="factron",
            version="0.1.0",
        )

    def execute_task(self, request: TaskRequest) -> TaskResponse:
        """Execute one validated FACTRON task."""
        result = self._agent_loop.run(
            run_id=request.run_id,
            task=request.task,
            context_state=request.context,
        )
        return TaskResponse.from_result(result)
