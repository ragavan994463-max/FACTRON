"""Knowledge ingestion pipeline for FACTRON."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

from .sources import KnowledgeSource


@dataclass(frozen=True, slots=True)
class IngestionResult:
    """Immutable result of source ingestion."""

    source_id: str
    success: bool
    content: str
    character_count: int
    metadata: Mapping[str, Any] = field(default_factory=dict)
    error: str | None = None

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError("source_id cannot be empty")

        if self.character_count < 0:
            raise ValueError(
                "character_count cannot be negative"
            )

        if self.success and self.error is not None:
            raise ValueError(
                "successful ingestion cannot contain an error"
            )

        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )


class KnowledgeIngestor:
    """Deterministic source ingestion coordinator.

    External loaders can be supplied through a resolver callback.
    FACTRON's core knowledge contracts remain independent of file,
    web, or third-party parsing libraries.
    """

    def __init__(
        self,
        resolver: Callable[[KnowledgeSource], str] | None = None,
    ) -> None:
        self._resolver = resolver

    def ingest(
        self,
        source: KnowledgeSource,
    ) -> IngestionResult:
        """Ingest one knowledge source."""
        if not isinstance(source, KnowledgeSource):
            raise TypeError(
                "source must be a KnowledgeSource"
            )

        try:
            if source.has_content:
                content = source.content
            elif self._resolver is not None:
                content = self._resolver(source)
            else:
                raise RuntimeError(
                    "Source has no inline content and no resolver "
                    "is configured."
                )

            if not isinstance(content, str):
                raise TypeError(
                    "resolver must return a string"
                )

            return IngestionResult(
                source_id=str(source.source_id),
                success=True,
                content=content,
                character_count=len(content),
                metadata=source.metadata,
            )

        except Exception as exc:
            return IngestionResult(
                source_id=str(source.source_id),
                success=False,
                content="",
                character_count=0,
                metadata=source.metadata,
                error=f"{type(exc).__name__}: {exc}",
            )
