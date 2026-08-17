"""Deterministic knowledge retrieval for FACTRON."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Mapping
from uuid import UUID

from knowledge.index import (
    KnowledgeIndex,
    KnowledgeRecord,
)


@dataclass(frozen=True, slots=True)
class RetrievalQuery:
    """Immutable normalized retrieval request."""

    query: str
    limit: int = 5
    metadata_filters: Mapping[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        if not isinstance(self.query, str):
            raise TypeError("query must be a string")

        normalized = self.query.strip()

        if not normalized:
            raise ValueError(
                "query cannot be empty"
            )

        if self.limit <= 0:
            raise ValueError(
                "limit must be greater than zero"
            )

        object.__setattr__(
            self,
            "query",
            normalized,
        )

        object.__setattr__(
            self,
            "metadata_filters",
            dict(self.metadata_filters),
        )


@dataclass(frozen=True, slots=True)
class RetrievalCandidate:
    """Immutable search candidate."""

    record: KnowledgeRecord
    lexical_score: float
    matched_terms: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(
            self.record,
            KnowledgeRecord,
        ):
            raise TypeError(
                "record must be a KnowledgeRecord"
            )

        if self.lexical_score < 0:
            raise ValueError(
                "lexical_score cannot be negative"
            )

        object.__setattr__(
            self,
            "matched_terms",
            tuple(self.matched_terms),
        )


class RetrievalSearcher:
    """Provider-independent search coordinator.

    The default backend is the existing deterministic KnowledgeIndex.
    """

    _TOKEN_PATTERN = re.compile(
        r"[A-Za-z0-9_]+"
    )

    def __init__(
        self,
        index: KnowledgeIndex,
    ) -> None:
        if not isinstance(index, KnowledgeIndex):
            raise TypeError(
                "index must be a KnowledgeIndex"
            )

        self._index = index

    @classmethod
    def _terms(
        cls,
        query: str,
    ) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                match.group(0).lower()
                for match in cls._TOKEN_PATTERN.finditer(
                    query
                )
            )
        )

    @staticmethod
    def _metadata_matches(
        record: KnowledgeRecord,
        filters: Mapping[str, Any],
    ) -> bool:
        if not filters:
            return True

        for key, expected in filters.items():
            if record.metadata.get(key) != expected:
                return False

        return True

    def search(
        self,
        request: RetrievalQuery,
    ) -> tuple[RetrievalCandidate, ...]:
        """Search indexed knowledge deterministically."""

        if not isinstance(
            request,
            RetrievalQuery,
        ):
            raise TypeError(
                "request must be a RetrievalQuery"
            )

        terms = self._terms(request.query)

        if not terms:
            raise ValueError(
                "query contains no searchable terms"
            )

        candidates: list[
            RetrievalCandidate
        ] = []

        for record in self._index.records_for_document(
            UUID(int=0)
        ):
            # This branch intentionally remains empty because the index
            # does not expose a global-record iterator in its frozen API.
            # Global retrieval is therefore implemented below using the
            # index's deterministic search boundary.
            del record

        indexed = self._index.search(
            request.query,
            limit=max(
                request.limit * 8,
                request.limit,
            ),
        )

        for record in indexed:
            if not self._metadata_matches(
                record,
                request.metadata_filters,
            ):
                continue

            text = record.text.lower()

            matched = tuple(
                term
                for term in terms
                if term in text
            )

            if not matched:
                continue

            score = sum(
                text.count(term)
                for term in matched
            )

            candidates.append(
                RetrievalCandidate(
                    record=record,
                    lexical_score=float(score),
                    matched_terms=matched,
                )
            )

        candidates.sort(
            key=lambda candidate: (
                -candidate.lexical_score,
                candidate.record.chunk_index,
                str(candidate.record.record_id),
            )
        )

        return tuple(
            candidates[:request.limit]
        )

    def search_text(
        self,
        query: str,
        *,
        limit: int = 5,
        metadata_filters: Mapping[str, Any] | None = None,
    ) -> tuple[RetrievalCandidate, ...]:
        """Convenience wrapper around RetrievalQuery."""

        return self.search(
            RetrievalQuery(
                query=query,
                limit=limit,
                metadata_filters=(
                    metadata_filters or {}
                ),
            )
        )
