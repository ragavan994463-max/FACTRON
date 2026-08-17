"""Planning contracts and deterministic planning for FACTRON Omega."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Protocol, runtime_checkable


class PlanStepStatus(str, Enum):
    """Lifecycle state of a planned step."""

    PENDING = "pending"
    READY = "ready"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class PlanStep:
    """Immutable description of one executable plan step."""

    step_id: str
    action: str
    arguments: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    status: PlanStepStatus = PlanStepStatus.PENDING

    def __post_init__(self) -> None:
        if not self.step_id.strip():
            raise ValueError("step_id cannot be empty")

        if not self.action.strip():
            raise ValueError("action cannot be empty")

        object.__setattr__(
            self,
            "arguments",
            dict(self.arguments),
        )

        if not isinstance(self.status, PlanStepStatus):
            raise TypeError(
                "status must be a PlanStepStatus"
            )


@dataclass(frozen=True, slots=True)
class Plan:
    """Immutable execution plan."""

    goal: str
    steps: tuple[PlanStep, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.goal.strip():
            raise ValueError("goal cannot be empty")

        normalized_steps = tuple(self.steps)

        for step in normalized_steps:
            if not isinstance(step, PlanStep):
                raise TypeError(
                    "all plan steps must be PlanStep instances"
                )

        object.__setattr__(
            self,
            "steps",
            normalized_steps,
        )

        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )


@dataclass(frozen=True, slots=True)
class PlanningContext:
    """Immutable input supplied to a planner."""

    task: str
    run_id: str
    state: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.task.strip():
            raise ValueError("task cannot be empty")

        if not self.run_id.strip():
            raise ValueError("run_id cannot be empty")

        object.__setattr__(
            self,
            "state",
            dict(self.state),
        )


@runtime_checkable
class Planner(Protocol):
    """Runtime-checkable planner interface."""

    def plan(
        self,
        context: PlanningContext,
    ) -> Plan:
        """Create an execution plan."""
        ...


class DeterministicPlanner:
    """Minimal deterministic planner.

    This planner intentionally performs no LLM call.

    It provides a stable foundation for later intelligence-driven
    planning while preserving the Agent architecture.
    """

    def plan(
        self,
        context: PlanningContext,
    ) -> Plan:
        if not isinstance(context, PlanningContext):
            raise TypeError(
                "context must be a PlanningContext"
            )

        step = PlanStep(
            step_id="step-1",
            action="observe",
            arguments={
                "task": context.task,
            },
            description=(
                "Observe the current task context before "
                "performing downstream actions."
            ),
            status=PlanStepStatus.READY,
        )

        return Plan(
            goal=context.task,
            steps=(step,),
            metadata={
                "planner": self.__class__.__name__,
                "run_id": context.run_id,
            },
        )
