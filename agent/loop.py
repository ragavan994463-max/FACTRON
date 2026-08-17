"""Controlled execution loop for FACTRON agents."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Mapping

from .executor import ExecutionContext, StepExecutor, StepStatus
from .planner import Plan, PlanStepStatus, Planner


class LoopStatus(StrEnum):
    """Final state of an agent run."""

    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class AgentRunResult:
    """Immutable summary of one complete agent run."""

    run_id: str
    status: LoopStatus
    outputs: tuple[Any, ...] = ()
    errors: tuple[str, ...] = ()
    completed_steps: int = 0
    failed_steps: int = 0


@dataclass(slots=True)
class AgentLoop:
    """Orchestrate planning and sequential step execution.

    This is the deterministic orchestration layer.  A future reasoning
    engine can produce the Plan, while this loop remains responsible for
    executing that plan and recording outcomes.
    """

    planner: Planner
    executor: StepExecutor
    max_steps: int = 32

    def run(
        self,
        *,
        run_id: str,
        task: str,
        context_state: Mapping[str, Any] | None = None,
    ) -> AgentRunResult:
        """Plan and execute a task with bounded step count."""
        if not run_id.strip():
            raise ValueError("run_id cannot be empty.")
        if not task.strip():
            raise ValueError("task cannot be empty.")
        if self.max_steps <= 0:
            raise ValueError("max_steps must be greater than zero.")

        context = ExecutionContext(
            run_id=run_id,
            task=task,
            state=dict(context_state or {}),
        )

        plan = self.planner.create_plan(task, context)

        if not plan.steps:
            return AgentRunResult(
                run_id=run_id,
                status=LoopStatus.BLOCKED,
            )

        outputs: list[Any] = []
        errors: list[str] = []
        completed = 0
        failed = 0

        for index, step in enumerate(plan.steps):
            if index >= self.max_steps:
                errors.append("Agent step limit reached.")
                return AgentRunResult(
                    run_id=run_id,
                    status=LoopStatus.FAILED,
                    outputs=tuple(outputs),
                    errors=tuple(errors),
                    completed_steps=completed,
                    failed_steps=failed,
                )

            if step.status is PlanStepStatus.SKIPPED:
                continue

            result = self.executor.execute(
                step.action,
                context,
                step.arguments,
            )

            if result.status is StepStatus.SUCCEEDED:
                step.status = PlanStepStatus.SUCCEEDED
                outputs.append(result.output)
                completed += 1
                context.state[f"step_{step.step_id}"] = result.output
            else:
                step.status = PlanStepStatus.FAILED
                failed += 1
                if result.error:
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
            status=LoopStatus.COMPLETED,
            outputs=tuple(outputs),
            errors=tuple(errors),
            completed_steps=completed,
            failed_steps=failed,
        )
