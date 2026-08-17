"""FACTRON Omega agent orchestration loop."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import uuid4
from typing import Any

from .executor import ExecutionContext, StepExecutor, StepStatus
from .planner import Plan, Planner, PlanningContext


class LoopStatus(str, Enum):
    """Overall AgentLoop state."""

    SUCCESS = "success"
    FAILED = "failed"
    EMPTY = "empty"


@dataclass(frozen=True, slots=True)
class AgentRunResult:
    """Immutable result of a complete agent run."""

    run_id: str
    status: LoopStatus
    outputs: tuple[Any, ...] = ()
    errors: tuple[str, ...] = ()
    completed_steps: int = 0
    failed_steps: int = 0


class AgentLoop:
    """Coordinates planning and execution.

    The loop contains no provider-specific intelligence. Planning and
    execution remain replaceable boundaries.
    """

    def __init__(
        self,
        planner: Planner,
        executor: StepExecutor,
        max_steps: int = 32,
    ) -> None:
        if not isinstance(executor, StepExecutor):
            raise TypeError("executor must be StepExecutor")

        if not isinstance(max_steps, int) or isinstance(max_steps, bool):
            raise TypeError("max_steps must be an integer")

        if max_steps <= 0:
            raise ValueError("max_steps must be greater than zero")

        if not isinstance(planner, Planner):
            raise TypeError("planner must implement Planner")

        self._planner = planner
        self._executor = executor
        self._max_steps = max_steps

    def run(
        self,
        task: str,
        state: dict[str, Any] | None = None,
    ) -> AgentRunResult:
        """Plan and execute one complete task."""
        if not task.strip():
            raise ValueError("task cannot be empty")

        run_id = str(uuid4())
        initial_state = dict(state or {})

        planning_context = PlanningContext(
            task=task,
            run_id=run_id,
            state=initial_state,
        )

        try:
            plan = self._planner.plan(planning_context)
        except Exception as exc:
            return AgentRunResult(
                run_id=run_id,
                status=LoopStatus.FAILED,
                errors=(f"PlanningError: {type(exc).__name__}: {exc}",),
            )

        if not isinstance(plan, Plan):
            return AgentRunResult(
                run_id=run_id,
                status=LoopStatus.FAILED,
                errors=("PlanningError: planner returned invalid Plan",),
            )

        if not plan.steps:
            return AgentRunResult(
                run_id=run_id,
                status=LoopStatus.EMPTY,
            )

        execution_context = ExecutionContext(
            run_id=run_id,
            task=task,
            state=initial_state,
            metadata=dict(plan.metadata),
        )

        outputs: list[Any] = []
        errors: list[str] = []
        completed = 0
        failed = 0

        for step_number, step in enumerate(plan.steps):
            if step_number >= self._max_steps:
                errors.append(
                    f"Maximum step limit reached: {self._max_steps}"
                )
                failed += 1
                break

            result = self._executor.execute(
                action=step.action,
                arguments=step.arguments,
                context=execution_context,
            )

            if result.status is StepStatus.SUCCESS:
                outputs.append(result.output)
                completed += 1
            else:
                failed += 1
                errors.append(
                    result.error or f"Step failed: {step.step_id}"
                )

        status = (
            LoopStatus.SUCCESS
            if failed == 0 and completed > 0
            else LoopStatus.FAILED
        )

        return AgentRunResult(
            run_id=run_id,
            status=status,
            outputs=tuple(outputs),
            errors=tuple(errors),
            completed_steps=completed,
            failed_steps=failed,
        )
