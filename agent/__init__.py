"""FACTRON agent subsystem.

The agent package provides the orchestration primitives for planning,
execution, observation, and controlled iteration.  Model-specific logic
remains outside this package so the architecture stays provider-agnostic.
"""

from .executor import (
    ExecutionContext,
    ExecutionResult,
    StepExecutor,
    StepStatus,
)
from .loop import AgentLoop, AgentRunResult, LoopStatus
from .planner import (
    Plan,
    PlanStep,
    PlanStepStatus,
    Planner,
    PlanningContext,
)

__all__ = [
    "AgentLoop",
    "AgentRunResult",
    "ExecutionContext",
    "ExecutionResult",
    "LoopStatus",
    "Plan",
    "PlanStep",
    "PlanStepStatus",
    "Planner",
    "PlanningContext",
    "StepExecutor",
    "StepStatus",
]
