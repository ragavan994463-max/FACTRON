"""Canonical knowledge-source contracts for FACTRON."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping
from uuid import UUID, uuid4


class SourceType(str, Enum):
    """Supported logical knowledge-source categories."""

    TEXT = "text"
    DOCUMENT = "document"
    WEB = "web"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DATASET = "dataset"
    CODE = "code"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class KnowledgeSource:
    """Immutable description of a knowledge source."""

    source_id: UUID = field(default_factory=uuid4)
    source_type: SourceType = SourceType.TEXT
    title: str = ""
    uri: str = ""
    content: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, UUID):
            raise TypeError("source_id must be a UUID")

        if not isinstance(self.source_type, SourceType):
            raise TypeError(
                "source_type must be a SourceType"
            )

        title = self.title.strip()
        uri = self.uri.strip()
        content = self.content

        if not title and not uri:
            raise ValueError(
                "KnowledgeSource requires title or uri"
            )

        if not content and not uri:
            raise ValueError(
                "KnowledgeSource requires content or uri"
            )

        object.__setattr__(self, "title", title)
        object.__setattr__(self, "uri", uri)
        object.__setattr__(self, "content", content)
        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )

    @property
    def has_content(self) -> bool:
        """Return whether source content is available."""
        return bool(self.content.strip())

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return {
            "source_id": str(self.source_id),
            "source_type": self.source_type.value,
            "title": self.title,
            "uri": self.uri,
            "content": self.content,
            "metadata": dict(self.metadata),
        }
