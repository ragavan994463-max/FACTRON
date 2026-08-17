"""Canonical FACTRON data contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from time import time
from typing import Any, Mapping
from uuid import uuid4


class TaskStatus(StrEnum):
    """Lifecycle status of a FACTRON task."""

    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class Evidence:
    """A traceable piece of evidence used by FACTRON reasoning."""

    content: str
    source: str
    confidence: float = 1.0
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.content.strip():
            raise ValueError("Evidence content cannot be empty.")
        if not self.source.strip():
            raise ValueError("Evidence source cannot be empty.")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Evidence confidence must be between 0 and 1.")


@dataclass(frozen=True, slots=True)
class KnowledgeItem:
    """Canonical representation of ingested knowledge."""

    item_id: str
    content: str
    source: str
    content_type: str
    created_at: float
    metadata: Mapping[str, Any] = field(default_factory=dict)
    confidence: float = 1.0

    @classmethod
    def create(
        cls,
        *,
        content: str,
        source: str,
        content_type: str,
        metadata: Mapping[str, Any] | None = None,
        confidence: float = 1.0,
    ) -> "KnowledgeItem":
        """Create a uniquely identified knowledge item."""
        return cls(
            item_id=str(uuid4()),
            content=content,
            source=source,
            content_type=content_type,
            created_at=time(),
            metadata=dict(metadata or {}),
            confidence=confidence,
        )

    def __post_init__(self) -> None:
        if not self.content.strip():
            raise ValueError("Knowledge content cannot be empty.")
        if not self.source.strip():
            raise ValueError("Knowledge source cannot be empty.")
        if not self.content_type.strip():
            raise ValueError("Knowledge content type cannot be empty.")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Knowledge confidence must be between 0 and 1.")


@dataclass(frozen=True, slots=True)
class Task:
    """Canonical task entering the FACTRON system."""

    task_id: str
    objective: str
    created_at: float
    metadata: Mapping[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.CREATED

    @classmethod
    def create(
        cls,
        objective: str,
        metadata: Mapping[str, Any] | None = None,
    ) -> "Task":
        """Create a new task."""
        if not objective.strip():
            raise ValueError("Task objective cannot be empty.")

        return cls(
            task_id=str(uuid4()),
            objective=objective,
            created_at=time(),
            metadata=dict(metadata or {}),
        )


@dataclass(frozen=True, slots=True)
class TaskResult:
    """Stable result contract for completed tasks."""

    task_id: str
    status: TaskStatus
    output: Any = None
    errors: tuple[str, ...] = ()
    evidence: tuple[Evidence, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
