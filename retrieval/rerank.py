"""Deterministic retrieval reranking for FACTRON."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .search import RetrievalCandidate


@dataclass(frozen=True, slots=True)
class RerankedResult:
    """Immutable reranked retrieval result."""

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
    """Apply deterministic relevance normalization.

    The reranker intentionally does not require embeddings or an LLM.
    A future semantic reranker can implement this boundary without
    changing the retrieval pipeline contract.
    """

    def __init__(
        self,
        *,
        exact_match_bonus: float = 0.15,
        multi_term_bonus: float = 0.10,
    ) -> None:
        if exact_match_bonus < 0:
            raise ValueError(
                "exact_match_bonus cannot be negative"
            )

        if multi_term_bonus < 0:
            raise ValueError(
                "multi_term_bonus cannot be negative"
            )

        self._exact_match_bonus = float(
            exact_match_bonus
        )
        self._multi_term_bonus = float(
            multi_term_bonus
        )

    def rerank(
        self,
        candidates: Iterable[
            RetrievalCandidate
        ],
    ) -> tuple[RerankedResult, ...]:
        """Rerank candidates into normalized [0, 1] scores."""

        candidate_list = tuple(candidates)

        if not candidate_list:
            return ()

        maximum = max(
            candidate.lexical_score
            for candidate in candidate_list
        )

        if maximum <= 0:
            maximum = 1.0

        scored: list[
            tuple[
                float,
                RetrievalCandidate,
            ]
        ] = []

        for candidate in candidate_list:
            base = (
                candidate.lexical_score
                / maximum
            )

            matched_count = len(
                candidate.matched_terms
            )

            multi_term_bonus = (
                self._multi_term_bonus
                if matched_count >= 2
                else 0.0
            )

            text_lower = (
                candidate.record.text.lower()
            )

            exact_match_bonus = (
                self._exact_match_bonus
                if any(
                    text_lower == term
                    for term in candidate.matched_terms
                )
                else 0.0
            )

            score = min(
                1.0,
                base
                + multi_term_bonus
                + exact_match_bonus,
            )

            scored.append(
                (score, candidate)
            )

        scored.sort(
            key=lambda item: (
                -item[0],
                item[1].record.chunk_index,
                str(item[1].record.record_id),
            )
        )

        return tuple(
            RerankedResult(
                candidate=candidate,
                score=score,
                rank=rank,
            )
            for rank, (score, candidate)
            in enumerate(
                scored,
                start=1,
            )
        )
