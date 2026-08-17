"""Planning contracts for FACTRON agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping, Protocol

from .executor import ExecutionContext


class PlanStepStatus(StrEnum):
    """Lifecycle states for a planned step."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(slots=True)
class PlanStep:
    """One atomic action in an agent plan."""

    step_id: str
    action: str
    arguments: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    status: PlanStepStatus = PlanStepStatus.PENDING

    def __post_init__(self) -> None:
        if not self.step_id.strip():
            raise ValueError("step_id cannot be empty.")
        if not self.action.strip():
            raise ValueError("action cannot be empty.")


@dataclass(frozen=True, slots=True)
class Plan:
    """Ordered execution plan."""

    goal: str
    steps: tuple[PlanStep, ...]
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.goal.strip():
            raise ValueError("Plan goal cannot be empty.")

        ids = [step.step_id for step in self.steps]
        if len(ids) != len(set(ids)):
            raise ValueError("Plan step IDs must be unique.")


@dataclass(frozen=True, slots=True)
class PlanningContext:
    """Read-only planning information."""

    task: str
    run_id: str
    state: Mapping[str, Any]


class Planner(Protocol):
    """Contract implemented by deterministic or model-backed planners."""

    def create_plan(
        self,
        task: str,
        context: ExecutionContext,
    ) -> Plan:
        """Create an executable plan for a task."""


class DeterministicPlanner:
    """Minimal planner used for infrastructure validation.

    Real reasoning will be connected later through FACTRON's intelligence
    layer.  This class exists only to prove that the orchestration boundary
    works before a model provider is introduced.
    """

    def create_plan(
        self,
        task: str,
        context: ExecutionContext,
    ) -> Plan:
        return Plan(
            goal=task,
            steps=(
                PlanStep(
                    step_id="validation-1",
                    action="factron.validate_task",
                    arguments={"task": task},
                    description="Validate that the agent received a task.",
                ),
            ),
            metadata={"planner": "deterministic"},
        )
