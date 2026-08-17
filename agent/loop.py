"""FACTRON Omega agent execution loop."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any
from uuid import uuid4

from .executor import ExecutionContext, StepExecutor, StepStatus
from .planner import Plan, Planner, PlanningContext


class LoopStatus(str, Enum):
    """Overall Agent run status."""

    SUCCESS = "success"
    FAILED = "failed"
    MAX_STEPS = "max_steps"


@dataclass(frozen=True, slots=True)
class AgentRunResult:
    """Final result of one Agent execution."""

    run_id: str
    status: LoopStatus
    outputs: tuple[Any, ...] = ()
    errors: tuple[str, ...] = ()
    completed_steps: int = 0
    failed_steps: int = 0

    @property
    def success(self) -> bool:
        """Return whether the Agent completed successfully."""
        return self.status is LoopStatus.SUCCESS


class AgentLoop:
    """Planner -> executor orchestration boundary."""

    def __init__(
        self,
        planner: Planner,
        executor: StepExecutor,
        max_steps: int = 32,
    ) -> None:
        if not hasattr(planner, "plan") or not callable(planner.plan):
            raise TypeError(
                "planner must provide a callable plan method"
            )

        if not isinstance(executor, StepExecutor):
            raise TypeError(
                "executor must be a StepExecutor"
            )

        if max_steps <= 0:
            raise ValueError(
                "max_steps must be greater than zero"
            )

        self._planner = planner
        self._executor = executor
        self._max_steps = max_steps

    def run(
        self,
        task: str,
        state: dict[str, Any] | None = None,
    ) -> AgentRunResult:
        """Plan and execute a task."""
        normalized_task = task.strip()

        if not normalized_task:
            raise ValueError("task cannot be empty")

        run_id = str(uuid4())

        mutable_state = dict(state or {})

        planning_context = PlanningContext(
            task=normalized_task,
            run_id=run_id,
            state=mutable_state,
        )

        plan: Plan = self._planner.plan(planning_context)

        if not isinstance(plan, Plan):
            raise TypeError(
                "planner.plan must return a Plan"
            )

        execution_context = ExecutionContext(
            run_id=run_id,
            task=normalized_task,
            state=mutable_state,
        )

        outputs: list[Any] = []
        errors: list[str] = []
        completed = 0
        failed = 0

        for position, step in enumerate(plan.steps):
            if position >= self._max_steps:
                return AgentRunResult(
                    run_id=run_id,
                    status=LoopStatus.MAX_STEPS,
                    outputs=tuple(outputs),
                    errors=tuple(errors),
                    completed_steps=completed,
                    failed_steps=failed,
                )

            result = self._executor.execute(
                action=step.action,
                arguments=step.arguments,
                context=execution_context,
            )

            if result.status is StepStatus.SUCCESS:
                completed += 1
                outputs.append(result.output)
            else:
                failed += 1

                if result.error is not None:
                    errors.append(result.error)

                return AgentRunResult(
                    run_id=run_id,
                    status=LoopStatus.FAILED,
                    outputs=tuple(outputs),
                    errors=tuple(errors),
                    completed_steps=completed,
                    failed_steps=failed,
                )

        return AgentRunResult(
            run_id=run_id,
            status=LoopStatus.SUCCESS,
            outputs=tuple(outputs),
            errors=tuple(errors),
            completed_steps=completed,
            failed_steps=failed,
        )
