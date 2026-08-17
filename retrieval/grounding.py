"""Knowledge grounding and context assembly for FACTRON."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .rerank import RerankedResult


@dataclass(frozen=True, slots=True)
class GroundingSource:
    """Auditable source attached to grounded context."""

    record_id: str
    document_id: str
    source_id: str
    rank: int
    score: float

    def __post_init__(self) -> None:
        if not self.record_id.strip():
            raise ValueError(
                "record_id cannot be empty"
            )

        if not self.document_id.strip():
            raise ValueError(
                "document_id cannot be empty"
            )

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


@dataclass(frozen=True, slots=True)
class GroundedContext:
    """Immutable retrieval context with source attribution."""

    query: str
    text: str
    sources: tuple[GroundingSource, ...] = ()

    def __post_init__(self) -> None:
        if not self.query.strip():
            raise ValueError(
                "query cannot be empty"
            )

        if not self.text.strip():
            raise ValueError(
                "grounded context text cannot be empty"
            )

        object.__setattr__(
            self,
            "sources",
            tuple(self.sources),
        )


class RetrievalGrounder:
    """Convert reranked retrieval results into auditable context."""

    def __init__(
        self,
        *,
        separator: str = "\n\n---\n\n",
    ) -> None:
        if not isinstance(separator, str):
            raise TypeError(
                "separator must be a string"
            )

        if not separator:
            raise ValueError(
                "separator cannot be empty"
            )

        self._separator = separator

    def ground(
        self,
        query: str,
        results: Iterable[
            RerankedResult
        ],
    ) -> GroundedContext:
        """Build a source-attributed context block."""

        if not isinstance(query, str):
            raise TypeError(
                "query must be a string"
            )

        normalized_query = query.strip()

        if not normalized_query:
            raise ValueError(
                "query cannot be empty"
            )

        result_list = tuple(results)

        if not result_list:
            raise ValueError(
                "cannot ground empty retrieval results"
            )

        blocks: list[str] = []
        sources: list[GroundingSource] = []

        for result in result_list:
            record = result.candidate.record

            blocks.append(
                (
                    f"[Source {result.rank}]\n"
                    f"{record.text.strip()}"
                )
            )

            sources.append(
                GroundingSource(
                    record_id=str(
                        record.record_id
                    ),
                    document_id=str(
                        record.document_id
                    ),
                    source_id=record.source_id,
                    rank=result.rank,
                    score=result.score,
                )
            )

        return GroundedContext(
            query=normalized_query,
            text=self._separator.join(blocks),
            sources=tuple(sources),
        )

    def ground_optional(
        self,
        query: str,
        results: Iterable[
            RerankedResult
        ],
    ) -> GroundedContext | None:
        """Return None when no retrieval results exist."""

        result_list = tuple(results)

        if not result_list:
            return None

        return self.ground(
            query,
            result_list,
        )
