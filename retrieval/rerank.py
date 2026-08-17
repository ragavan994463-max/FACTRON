"""Deterministic retrieval reranking for FACTRON Omega."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .search import RetrievalCandidate


@dataclass(frozen=True, slots=True)
class RerankedResult:
    """A retrieval candidate after deterministic reranking."""

    candidate: RetrievalCandidate
    score: float
    rank: int

    def __post_init__(self) -> None:
        if not isinstance(
            self.candidate,
            RetrievalCandidate,
        ):
            raise TypeError(
                "candidate must be a RetrievalCandidate"
            )

        if not 0.0 <= self.score <= 1.0:
            raise ValueError(
                "score must be between 0 and 1"
            )

        if self.rank <= 0:
            raise ValueError(
                "rank must be greater than zero"
            )


class RetrievalReranker:
    """Provider-independent deterministic reranker.

    Current scoring combines:

    1. lexical frequency
    2. query-term coverage
    3. deterministic tie-breaking

    This is intentionally lightweight. A learned reranker can
    replace this implementation later behind the same boundary.
    """

    def rerank(
        self,
        candidates: tuple[RetrievalCandidate, ...] | list[RetrievalCandidate],
        limit: int | None = None,
    ) -> tuple[RerankedResult, ...]:
        """Rerank retrieval candidates deterministically."""

        candidate_list = list(candidates)

        for candidate in candidate_list:
            if not isinstance(
                candidate,
                RetrievalCandidate,
            ):
                raise TypeError(
                    "all candidates must be RetrievalCandidate instances"
                )

        if limit is not None and limit <= 0:
            raise ValueError(
                "limit must be greater than zero"
            )

        if not candidate_list:
            return ()

        max_lexical = max(
            candidate.lexical_score
            for candidate in candidate_list
        )

        max_coverage = max(
            len(candidate.matched_terms)
            for candidate in candidate_list
        )

        def score(candidate: RetrievalCandidate) -> float:
            lexical_component = (
                candidate.lexical_score / max_lexical
                if max_lexical > 0
                else 0.0
            )

            coverage_component = (
                len(candidate.matched_terms) / max_coverage
                if max_coverage > 0
                else 0.0
            )

            combined = (
                lexical_component * 0.70
                + coverage_component * 0.30
            )

            return max(
                0.0,
                min(1.0, combined),
            )

        scored: list[
            tuple[float, RetrievalCandidate]
        ] = [
            (score(candidate), candidate)
            for candidate in candidate_list
        ]

        scored.sort(
            key=lambda item: (
                -item[0],
                -item[1].lexical_score,
                item[1].record.chunk_index,
                str(item[1].record.record_id),
            )
        )

        if limit is not None:
            scored = scored[:limit]

        results: list[RerankedResult] = []

        for position, (item_score, candidate) in enumerate(
            scored,
            start=1,
        ):
            results.append(
                RerankedResult(
                    candidate=candidate,
                    score=item_score,
                    rank=position,
                )
            )

        return tuple(results)
