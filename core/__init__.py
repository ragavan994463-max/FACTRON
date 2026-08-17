"""FACTRON core package.

The core layer contains stable contracts shared by all FACTRON subsystems.
It must remain independent from model providers, databases, web frameworks,
and external tooling.
"""

from .config import FactronConfig, ModelConfig, RuntimeConfig
from .events import Event, EventBus, EventType
from .schemas import (
    Evidence,
    KnowledgeItem,
    Task,
    TaskResult,
)
from .state import FactronState, StateSnapshot

__all__ = [
    "Event",
    "EventBus",
    "EventType",
    "Evidence",
    "FactronConfig",
    "FactronState",
    "KnowledgeItem",
    "ModelConfig",
    "RuntimeConfig",
    "StateSnapshot",
    "Task",
    "TaskResult",
]
