"""FACTRON Omega Agent subsystem.

The Agent subsystem coordinates:

    planning
        ↓
    execution
        ↓
    observation
        ↓
    loop control

The implementation is provider-independent and deliberately
separated from intelligence, knowledge, memory, retrieval,
tools, and application layers.

No model provider is hard-coded here.
"""

from .planner import (
    PlanStepStatus,
    PlanStep,
    Plan,
    PlanningContext,
    Planner,
    DeterministicPlanner,
)

from .executor import (
    StepStatus,
    StepAction,
    ExecutionContext,
    ExecutionResult,
    StepExecutor,
)

from .loop import (
    LoopStatus,
    AgentRunResult,
    AgentLoop,
)


__all__ = [
    "PlanStepStatus",
    "PlanStep",
    "Plan",
    "PlanningContext",
    "Planner",
    "DeterministicPlanner",
    "StepStatus",
    "StepAction",
    "ExecutionContext",
    "ExecutionResult",
    "StepExecutor",
    "LoopStatus",
    "AgentRunResult",
    "AgentLoop",
]
