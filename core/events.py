"""FACTRON event system.

Events provide a lightweight internal communication mechanism between
subsystems without creating direct coupling between every component.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from enum import StrEnum
from threading import RLock
from time import time
from typing import Any, Callable, DefaultDict
from uuid import uuid4


class EventType(StrEnum):
    """Canonical FACTRON lifecycle events."""

    SYSTEM_STARTED = "system.started"
    TASK_CREATED = "task.created"
    TASK_COMPLETED = "task.completed"
    KNOWLEDGE_INGESTED = "knowledge.ingested"
    MEMORY_UPDATED = "memory.updated"
    RETRIEVAL_COMPLETED = "retrieval.completed"
    AGENT_ACTION = "agent.action"
    EVALUATION_COMPLETED = "evaluation.completed"
    LEARNING_COMPLETED = "learning.completed"
    ERROR = "system.error"


@dataclass(frozen=True, slots=True)
class Event:
    """Immutable event envelope."""

    event_id: str
    event_type: EventType
    payload: dict[str, Any]
    timestamp: float
    source: str

    @classmethod
    def create(
        cls,
        event_type: EventType,
        payload: dict[str, Any] | None = None,
        *,
        source: str = "factron",
    ) -> "Event":
        """Create a new event with generated identity and timestamp."""
        if not source.strip():
            raise ValueError("Event source cannot be empty.")

        return cls(
            event_id=str(uuid4()),
            event_type=event_type,
            payload=dict(payload or {}),
            timestamp=time(),
            source=source,
        )


EventHandler = Callable[[Event], None]


class EventBus:
    """Thread-safe in-process publish/subscribe event bus."""

    def __init__(self) -> None:
        self._handlers: DefaultDict[EventType, list[EventHandler]] = defaultdict(list)
        self._lock = RLock()

    def subscribe(
        self,
        event_type: EventType,
        handler: EventHandler,
    ) -> None:
        """Subscribe a handler to an event type."""
        if not callable(handler):
            raise TypeError("handler must be callable.")

        with self._lock:
            if handler not in self._handlers[event_type]:
                self._handlers[event_type].append(handler)

    def unsubscribe(
        self,
        event_type: EventType,
        handler: EventHandler,
    ) -> None:
        """Remove a previously registered handler."""
        with self._lock:
            handlers = self._handlers.get(event_type, [])
            if handler in handlers:
                handlers.remove(handler)

    def publish(self, event: Event) -> int:
        """Publish an event and return the number of invoked handlers."""
        with self._lock:
            handlers = tuple(self._handlers.get(event.event_type, ()))

        invoked = 0

        for handler in handlers:
            handler(event)
            invoked += 1

        return invoked

    def clear(self) -> None:
        """Remove all subscriptions."""
        with self._lock:
            self._handlers.clear()
