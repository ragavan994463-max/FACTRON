"""Experience contracts and bounded experience storage for FACTRON."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import UUID, uuid4


class ExperienceOutcome(str, Enum):
    """Canonical high-level execution outcome."""

    SUCCESS = "success"
    PARTIAL = "partial"
    FAILURE = "failure"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Experience:
    """Immutable record describing one FACTRON execution experience."""

    experience_id: UUID = field(default_factory=uuid4)
    task: str = ""
    input_data: Any = None
    output_data: Any = None
    outcome: ExperienceOutcome = ExperienceOutcome.UNKNOWN
    reward: float = 0.0
    success: bool = False
    duration_ms: float = 0.0
    metadata: Mapping[str, Any] = field(default_factory=dict)
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __post_init__(self) -> None:
        if not isinstance(self.experience_id, UUID):
            raise TypeError("experience_id must be a UUID")

        if not isinstance(self.task, str):
            raise TypeError("task must be a string")

        if not self.task.strip():
            raise ValueError("task cannot be empty")

        if not isinstance(self.outcome, ExperienceOutcome):
            raise TypeError(
                "outcome must be an ExperienceOutcome"
            )

        if not isinstance(self.reward, (int, float)):
            raise TypeError("reward must be numeric")

        if not isinstance(self.duration_ms, (int, float)):
            raise TypeError("duration_ms must be numeric")

        if self.duration_ms < 0:
            raise ValueError(
                "duration_ms cannot be negative"
            )

        if not isinstance(self.created_at, datetime):
            raise TypeError(
                "created_at must be a datetime"
            )

        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )

    @property
    def normalized_reward(self) -> float:
        """Return reward bounded to the canonical [0, 1] range."""

        return max(
            0.0,
            min(
                1.0,
                float(self.reward),
            ),
        )


class ExperienceStore:
    """Deterministic bounded in-memory experience store.

    The storage boundary is replaceable later by persistent or
    distributed memory implementations without changing Experience.
    """

    def __init__(self, max_size: int = 10_000) -> None:
        if max_size <= 0:
            raise ValueError(
                "max_size must be greater than zero"
            )

        self._max_size = max_size
        self._experiences: dict[UUID, Experience] = {}
        self._order: list[UUID] = []

    @property
    def size(self) -> int:
        """Return current number of stored experiences."""

        return len(self._experiences)

    @property
    def max_size(self) -> int:
        """Return configured capacity."""

        return self._max_size

    def add(self, experience: Experience) -> UUID:
        """Insert or replace an experience."""

        if not isinstance(experience, Experience):
            raise TypeError(
                "experience must be an Experience"
            )

        experience_id = experience.experience_id

        if experience_id in self._experiences:
            self._experiences[experience_id] = experience
            return experience_id

        self._experiences[experience_id] = experience
        self._order.append(experience_id)

        while len(self._order) > self._max_size:
            oldest_id = self._order.pop(0)
            self._experiences.pop(oldest_id, None)

        return experience_id

    def get(
        self,
        experience_id: UUID,
    ) -> Experience | None:
        """Retrieve an experience by identifier."""

        if not isinstance(experience_id, UUID):
            raise TypeError(
                "experience_id must be a UUID"
            )

        return self._experiences.get(experience_id)

    def recent(
        self,
        limit: int = 10,
    ) -> tuple[Experience, ...]:
        """Return recent experiences, newest first."""

        if limit <= 0:
            raise ValueError(
                "limit must be greater than zero"
            )

        return tuple(
            self._experiences[experience_id]
            for experience_id in reversed(
                self._order[-limit:]
            )
            if experience_id in self._experiences
        )

    def successful(
        self,
        limit: int = 10,
    ) -> tuple[Experience, ...]:
        """Return recent successful experiences."""

        if limit <= 0:
            raise ValueError(
                "limit must be greater than zero"
            )

        matches: list[Experience] = []

        for experience_id in reversed(self._order):
            experience = self._experiences.get(
                experience_id
            )

            if experience is not None and experience.success:
                matches.append(experience)

            if len(matches) >= limit:
                break

        return tuple(matches)

    def clear(self) -> None:
        """Remove every stored experience."""

        self._experiences.clear()
        self._order.clear()
