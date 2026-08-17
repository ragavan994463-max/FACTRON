"""Knowledge normalization and chunking for FACTRON."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Mapping
from uuid import UUID, uuid4

from .ingest import IngestionResult


@dataclass(frozen=True, slots=True)
class KnowledgeDocument:
    """Immutable normalized knowledge document."""

    document_id: UUID = field(default_factory=uuid4)
    source_id: str = ""
    title: str = ""
    text: str = ""
    chunks: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError(
                "source_id cannot be empty"
            )

        if not self.text.strip():
            raise ValueError(
                "document text cannot be empty"
            )

        normalized_chunks = tuple(
            chunk.strip()
            for chunk in self.chunks
            if chunk.strip()
        )

        if not normalized_chunks:
            raise ValueError(
                "document must contain at least one chunk"
            )

        object.__setattr__(
            self,
            "chunks",
            normalized_chunks,
        )

        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )


class KnowledgeProcessor:
    """Normalizes and deterministically chunks knowledge."""

    def __init__(
        self,
        chunk_size: int = 1200,
        chunk_overlap: int = 150,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError(
                "chunk_size must be greater than zero"
            )

        if chunk_overlap < 0:
            raise ValueError(
                "chunk_overlap cannot be negative"
            )

        if chunk_overlap >= chunk_size:
            raise ValueError(
                "chunk_overlap must be smaller than chunk_size"
            )

        self._chunk_size = chunk_size
        self._chunk_overlap = chunk_overlap

    @staticmethod
    def normalize(text: str) -> str:
        """Normalize whitespace without changing semantic content."""
        if not isinstance(text, str):
            raise TypeError("text must be a string")

        text = text.replace("\r\n", "\n")
        text = text.replace("\r", "\n")

        lines = [
            re.sub(r"[ \t]+", " ", line).strip()
            for line in text.split("\n")
        ]

        cleaned = "\n".join(
            line for line in lines if line
        )

        return cleaned.strip()

    def chunk(self, text: str) -> tuple[str, ...]:
        """Split normalized text into deterministic overlapping chunks."""
        normalized = self.normalize(text)

        if not normalized:
            return ()

        if len(normalized) <= self._chunk_size:
            return (normalized,)

        chunks: list[str] = []
        start = 0
        text_length = len(normalized)

        while start < text_length:
            end = min(
                start + self._chunk_size,
                text_length,
            )

            chunk = normalized[start:end].strip()

            if chunk:
                chunks.append(chunk)

            if end >= text_length:
                break

            next_start = end - self._chunk_overlap

            if next_start <= start:
                raise RuntimeError(
                    "Chunker failed to make forward progress"
                )

            start = next_start

        return tuple(chunks)

    def process(
        self,
        result: IngestionResult,
        title: str = "",
    ) -> KnowledgeDocument:
        """Convert an ingestion result into a document."""
        if not isinstance(result, IngestionResult):
            raise TypeError(
                "result must be an IngestionResult"
            )

        if not result.success:
            raise ValueError(
                f"Cannot process failed ingestion: {result.error}"
            )

        normalized = self.normalize(result.content)
        chunks = self.chunk(normalized)

        if not normalized or not chunks:
            raise ValueError(
                "Ingested content contains no usable text"
            )

        return KnowledgeDocument(
            source_id=result.source_id,
            title=title.strip(),
            text=normalized,
            chunks=chunks,
            metadata=result.metadata,
        )
