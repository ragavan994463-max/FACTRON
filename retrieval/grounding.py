"""Grounded context construction for FACTRON Omega."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from uuid import UUID


@dataclass(frozen=True, slots=True)
class GroundingSource:
    """Auditable source attribution for grounded context."""

    record_id: UUID
    document_id: UUID
    source_id: str
    rank: int
    score: float
    chunk_index: int
    metadata: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.record_id, UUID):
            raise TypeError("record_id must be a UUID")

        if not isinstance(self.document_id, UUID):
            raise TypeError("document_id must be a UUID")

        if not self.source_id.strip():
            raise ValueError(
                "source_id cannot be empty"
            )

        if self.rank <= 0:
            raise ValueError(
                "rank must be greater than zero"
            )

        if not 0.0 <= self.score <= 1.0:
            raise ValueError(
                "score must be between 0 and 1"
            )

        if self.chunk_index < 0:
            raise ValueError(
                "chunk_index cannot be negative"
            )

        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )


@dataclass(frozen=True, slots=True)
class GroundedContext:
    """Immutable, auditable context prepared for downstream reasoning."""

    query: str
    text: str
    sources: tuple[GroundingSource, ...]

    def __post_init__(self) -> None:
        if not self.query.strip():
            raise ValueError(
                "query cannot be empty"
            )

        if not self.text.strip():
            raise ValueError(
                "grounded text cannot be empty"
            )

        object.__setattr__(
            self,
            "query",
            self.query.strip(),
        )

        object.__setattr__(
            self,
            "text",
            self.text.strip(),
        )

        object.__setattr__(
            self,
            "sources",
            tuple(self.sources),
        )


class RetrievalGrounder:
    """Build deterministic, auditable context from reranked results."""

    def ground(
        self,
        query: str,
        results: tuple[Any, ...] | list[Any],
        max_chars: int = 12000,
    ) -> GroundedContext:
        """Construct grounded context from reranked results."""

        from .rerank import RerankedResult

        normalized_query = query.strip()

        if not normalized_query:
            raise ValueError(
                "query cannot be empty"
            )

        if max_chars <= 0:
            raise ValueError(
                "max_chars must be greater than zero"
            )

        result_list = list(results)

        for result in result_list:
            if not isinstance(result, RerankedResult):
                raise TypeError(
                    "all results must be RerankedResult instances"
                )

        if not result_list:
            raise ValueError(
                "cannot ground an empty result set"
            )

        sections: list[str] = []
        sources: list[GroundingSource] = []
        current_length = 0

        for result in result_list:
            record = result.candidate.record

            source_header = (
                f"[Source {result.rank}] "
                f"source_id={record.source_id} "
                f"document_id={record.document_id} "
                f"chunk={record.chunk_index} "
                f"score={result.score:.4f}"
            )

            section = (
                source_header
                + "\n"
                + record.text.strip()
            )

            separator_length = (
                2 if sections else 0
            )

            if (
                current_length
                + separator_length
                + len(section)
                > max_chars
            ):
                remaining = (
                    max_chars
                    - current_length
                    - separator_length
                )

                if remaining <= 0:
                    break

                truncated = section[:remaining].rstrip()

                if truncated:
                    sections.append(truncated)
                    current_length += (
                        separator_length
                        + len(truncated)
                    )

                break

            sections.append(section)
            current_length += (
                separator_length
                + len(section)
            )

            sources.append(
                GroundingSource(
                    record_id=record.record_id,
                    document_id=record.document_id,
                    source_id=record.source_id,
                    rank=result.rank,
                    score=result.score,
                    chunk_index=record.chunk_index,
                    metadata=record.metadata,
                )
            )

        if not sections:
            raise ValueError(
                "no context could be constructed within max_chars"
            )

        return GroundedContext(
            query=normalized_query,
            text="\n\n".join(sections),
            sources=tuple(sources),
        )

    def ground_optional(
        self,
        query: str,
        results: tuple[Any, ...] | list[Any],
        max_chars: int = 12000,
    ) -> GroundedContext | None:
        """Return grounded context or None for an empty result set."""

        if not results:
            return None

        return self.ground(
            query=query,
            results=results,
            max_chars=max_chars,
        )
