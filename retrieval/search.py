"""Deterministic knowledge retrieval for FACTRON Omega."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any, Mapping

from knowledge.index import KnowledgeIndex, KnowledgeRecord


@dataclass(frozen=True, slots=True)
class RetrievalQuery:
    """Immutable retrieval request."""

    query: str
    limit: int = 5
    metadata_filters: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        normalized = self.query.strip()

        if not normalized:
            raise ValueError("query cannot be empty")

        if self.limit <= 0:
            raise ValueError("limit must be greater than zero")

        object.__setattr__(self, "query", normalized)
        object.__setattr__(
            self,
            "metadata_filters",
            dict(self.metadata_filters),
        )


@dataclass(frozen=True, slots=True)
class RetrievalCandidate:
    """A knowledge record selected by retrieval."""

    record: KnowledgeRecord
    lexical_score: float
    matched_terms: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.record, KnowledgeRecord):
            raise TypeError("record must be a KnowledgeRecord")

        if self.lexical_score < 0:
            raise ValueError("lexical_score cannot be negative")

        object.__setattr__(
            self,
            "matched_terms",
            tuple(
                term.strip().lower()
                for term in self.matched_terms
                if term.strip()
            ),
        )


class RetrievalSearcher:
    """Deterministic lexical retrieval adapter.

    The searcher depends only on the KnowledgeIndex contract.
    No LLM, embedding model, vector database, or provider API
    is required.
    """

    _TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")

    def __init__(self, index: KnowledgeIndex) -> None:
        if not isinstance(index, KnowledgeIndex):
            raise TypeError("index must be a KnowledgeIndex")

        self._index = index

    @classmethod
    def _tokenize(cls, text: str) -> tuple[str, ...]:
        return tuple(
            token.lower()
            for token in cls._TOKEN_PATTERN.findall(text)
            if token.strip()
        )

    @staticmethod
    def _metadata_matches(
        record: KnowledgeRecord,
        filters: Mapping[str, Any],
    ) -> bool:
        if not filters:
            return True

        metadata = record.metadata

        return all(
            metadata.get(key) == expected
            for key, expected in filters.items()
        )

    def search(
        self,
        request: RetrievalQuery,
    ) -> tuple[RetrievalCandidate, ...]:
        """Execute deterministic lexical retrieval."""

        if not isinstance(request, RetrievalQuery):
            raise TypeError(
                "request must be a RetrievalQuery"
            )

        query_terms = self._tokenize(request.query)

        if not query_terms:
            return ()

        # The KnowledgeIndex remains the source of indexed truth.
        #
        # Requesting a bounded but sufficiently broad candidate pool
        # keeps the retrieval layer independent from the index's
        # internal storage representation.
        candidate_limit = max(
            request.limit * 20,
            100,
        )

        records = self._index.search(
            request.query,
            limit=candidate_limit,
        )

        candidates: list[RetrievalCandidate] = []

        for record in records:
            if not self._metadata_matches(
                record,
                request.metadata_filters,
            ):
                continue

            tokens = self._tokenize(record.text)
            token_set = set(tokens)

            matched = tuple(
                term
                for term in query_terms
                if term in token_set
            )

            if not matched:
                continue

            text_lower = record.text.lower()

            lexical_score = float(
                sum(
                    text_lower.count(term)
                    for term in matched
                )
            )

            candidates.append(
                RetrievalCandidate(
                    record=record,
                    lexical_score=lexical_score,
                    matched_terms=matched,
                )
            )

        candidates.sort(
            key=lambda candidate: (
                -candidate.lexical_score,
                -len(candidate.matched_terms),
                candidate.record.chunk_index,
                str(candidate.record.record_id),
            )
        )

        return tuple(candidates[: request.limit])

    def search_text(
        self,
        query: str,
        limit: int = 5,
        metadata_filters: Mapping[str, Any] | None = None,
    ) -> tuple[RetrievalCandidate, ...]:
        """Convenience API for direct text retrieval."""

        return self.search(
            RetrievalQuery(
                query=query,
                limit=limit,
                metadata_filters=(
                    metadata_filters
                    if metadata_filters is not None
                    else {}
                ),
            )
        )
