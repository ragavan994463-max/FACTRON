"""FACTRON Omega deterministic planning subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class PlanStepStatus(str, Enum):
    """Lifecycle status for a planned step."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class PlanStep:
    """One executable step in an Agent plan."""

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

        if not normalized_steps:
            raise ValueError("plan must contain at least one step")

        seen: set[str] = set()

        for step in normalized_steps:
            if not isinstance(step, PlanStep):
                raise TypeError("all plan steps must be PlanStep instances")

            if step.step_id in seen:
                raise ValueError(
                    f"duplicate step_id: {step.step_id}"
                )

            seen.add(step.step_id)

        object.__setattr__(self, "steps", normalized_steps)
        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True, slots=True)
class PlanningContext:
    """Context supplied to a planner."""

    task: str
    run_id: str
    state: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not self.task.strip():
            raise ValueError("task cannot be empty")

        if not self.run_id.strip():
            raise ValueError("run_id cannot be empty")

        object.__setattr__(self, "state", dict(self.state))


class Planner:
    """Planner protocol boundary."""

    def plan(self, context: PlanningContext) -> Plan:
        """Create an execution plan."""
        raise NotImplementedError


class DeterministicPlanner(Planner):
    """Simple deterministic planner for architecture validation.

    The planner deliberately does not call an LLM.
    Real reasoning can be connected above this boundary later.
    """

    def plan(self, context: PlanningContext) -> Plan:
        if not isinstance(context, PlanningContext):
            raise TypeError(
                "context must be a PlanningContext"
            )

        task = context.task.strip()

        return Plan(
            goal=task,
            steps=(
                PlanStep(
                    step_id="step-1",
                    action="record_task",
                    arguments={"task": task},
                    description="Record the requested task.",
                ),
            ),
            metadata={
                "planner": "deterministic",
                "run_id": context.run_id,
            },
        )
