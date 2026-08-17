"""Agent planning/execution loop for FACTRON Omega."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any
from uuid import uuid4

from .executor import (
    ExecutionContext,
    StepExecutor,
    StepStatus,
)
from .planner import (
    PlanStepStatus,
    Planner,
    PlanningContext,
)


class LoopStatus(str, Enum):
    """Overall Agent run status."""

    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    EMPTY = "empty"


@dataclass(frozen=True, slots=True)
class AgentRunResult:
    """Immutable summary of an Agent run."""

    run_id: str
    status: LoopStatus
    outputs: tuple[Any, ...] = ()
    errors: tuple[str, ...] = ()
    completed_steps: int = 0
    failed_steps: int = 0

    def __post_init__(self) -> None:
        if not self.run_id.strip():
            raise ValueError(
                "run_id cannot be empty"
            )

        object.__setattr__(
            self,
            "outputs",
            tuple(self.outputs),
        )

        object.__setattr__(
            self,
            "errors",
            tuple(self.errors),
        )

        if self.completed_steps < 0:
            raise ValueError(
                "completed_steps cannot be negative"
            )

        if self.failed_steps < 0:
            raise ValueError(
                "failed_steps cannot be negative"
            )


class AgentLoop:
    """Coordinates planning and execution."""

    def __init__(
        self,
        planner: Planner,
        executor: StepExecutor,
        max_steps: int = 32,
    ) -> None:
        if not isinstance(executor, StepExecutor):
            raise TypeError(
                "executor must be a StepExecutor"
            )

        if not isinstance(max_steps, int):
            raise TypeError(
                "max_steps must be an integer"
            )

        if max_steps <= 0:
            raise ValueError(
                "max_steps must be greater than zero"
            )

        if not isinstance(planner, Planner):
            raise TypeError(
                "planner must satisfy the Planner protocol"
            )

        self.planner = planner
        self.executor = executor
        self.max_steps = max_steps

    def run(
        self,
        task: str,
        state: dict[str, Any] | None = None,
        run_id: str | None = None,
    ) -> AgentRunResult:
        """Plan and execute one Agent run."""
        if not isinstance(task, str):
            raise TypeError("task must be a string")

        if not task.strip():
            raise ValueError("task cannot be empty")

        actual_run_id = (
            run_id.strip()
            if isinstance(run_id, str) and run_id.strip()
            else str(uuid4())
        )

        initial_state = dict(state or {})

        planning_context = PlanningContext(
            task=task,
            run_id=actual_run_id,
            state=initial_state,
        )

        plan = self.planner.plan(planning_context)

        if not plan.steps:
            return AgentRunResult(
                run_id=actual_run_id,
                status=LoopStatus.EMPTY,
            )

        if len(plan.steps) > self.max_steps:
            raise ValueError(
                "Plan exceeds configured max_steps"
            )

        execution_context = ExecutionContext(
            run_id=actual_run_id,
            task=task,
            state=initial_state,
            metadata={
                "goal": plan.goal,
                **dict(plan.metadata),
            },
        )

        outputs: list[Any] = []
        errors: list[str] = []
        completed = 0
        failed = 0

        for step in plan.steps:
            if step.status is PlanStepStatus.SKIPPED:
                continue

            result = self.executor.execute(
                action_name=step.action,
                arguments=dict(step.arguments),
                context=execution_context,
            )

            if result.status is StepStatus.SUCCESS:
                completed += 1
                outputs.append(result.output)
            else:
                failed += 1

                if result.error:
                    errors.append(result.error)

        if failed == 0:
            status = LoopStatus.SUCCESS
        elif completed == 0:
            status = LoopStatus.FAILED
        else:
            status = LoopStatus.PARTIAL

        return AgentRunResult(
            run_id=actual_run_id,
            status=status,
            outputs=tuple(outputs),
            errors=tuple(errors),
            completed_steps=completed,
            failed_steps=failed,
        )
