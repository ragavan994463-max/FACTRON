"""Deterministic evaluation engine for FACTRON learning."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .experience import Experience


class EvaluationStatus(str, Enum):
    """Evaluation classification."""

    ACCEPTED = "accepted"
    REVIEW = "review"
    REJECTED = "rejected"


class EvaluationDimension(str, Enum):
    """Measurable evaluation dimensions."""

    SUCCESS = "success"
    REWARD = "reward"
    EFFICIENCY = "efficiency"


@dataclass(frozen=True, slots=True)
class Evaluation:
    """Immutable evaluation signal."""

    experience_id: str
    overall_score: float
    status: EvaluationStatus
    scores: dict[str, float]
    strengths: tuple[str, ...] = ()
    weaknesses: tuple[str, ...] = ()
    rationale: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.experience_id, str):
            raise TypeError(
                "experience_id must be a string"
            )

        if not self.experience_id.strip():
            raise ValueError(
                "experience_id cannot be empty"
            )

        if not 0.0 <= self.overall_score <= 1.0:
            raise ValueError(
                "overall_score must be between 0 and 1"
            )

        if not isinstance(
            self.status,
            EvaluationStatus,
        ):
            raise TypeError(
                "status must be an EvaluationStatus"
            )

        normalized_scores: dict[str, float] = {}

        for name, value in self.scores.items():
            score = float(value)

            if not 0.0 <= score <= 1.0:
                raise ValueError(
                    f"score for {name!r} must be between 0 and 1"
                )

            normalized_scores[str(name)] = score

        object.__setattr__(
            self,
            "scores",
            normalized_scores,
        )

        object.__setattr__(
            self,
            "strengths",
            tuple(self.strengths),
        )

        object.__setattr__(
            self,
            "weaknesses",
            tuple(self.weaknesses),
        )


class LearningEvaluator:
    """Evaluate measurable execution properties.

    No provider call is performed here. The evaluator works entirely
    from observable experience fields.
    """

    def __init__(
        self,
        *,
        success_weight: float = 0.45,
        reward_weight: float = 0.35,
        efficiency_weight: float = 0.20,
    ) -> None:
        weights = (
            float(success_weight),
            float(reward_weight),
            float(efficiency_weight),
        )

        if any(weight < 0 for weight in weights):
            raise ValueError(
                "evaluation weights cannot be negative"
            )

        total = sum(weights)

        if total <= 0:
            raise ValueError(
                "evaluation weights must have positive total"
            )

        self._success_weight = (
            weights[0] / total
        )
        self._reward_weight = (
            weights[1] / total
        )
        self._efficiency_weight = (
            weights[2] / total
        )

    @staticmethod
    def _efficiency_score(
        duration_ms: float,
    ) -> float:
        """Convert duration into a bounded efficiency score."""

        if duration_ms <= 0:
            return 1.0

        return max(
            0.0,
            min(
                1.0,
                1.0 - (
                    float(duration_ms) / 5000.0
                ),
            ),
        )

    def evaluate(
        self,
        experience: Experience,
    ) -> Evaluation:
        """Evaluate one experience."""

        if not isinstance(experience, Experience):
            raise TypeError(
                "experience must be an Experience"
            )

        success_score = (
            1.0 if experience.success else 0.0
        )

        reward_score = experience.normalized_reward

        efficiency_score = self._efficiency_score(
            experience.duration_ms
        )

        overall_score = (
            success_score * self._success_weight
            + reward_score * self._reward_weight
            + efficiency_score * self._efficiency_weight
        )

        scores = {
            EvaluationDimension.SUCCESS.value:
                success_score,
            EvaluationDimension.REWARD.value:
                reward_score,
            EvaluationDimension.EFFICIENCY.value:
                efficiency_score,
        }

        strengths: list[str] = []
        weaknesses: list[str] = []

        if success_score >= 0.8:
            strengths.append("task_success")
        else:
            weaknesses.append("task_success")

        if reward_score >= 0.7:
            strengths.append("reward_quality")
        elif reward_score < 0.4:
            weaknesses.append("reward_quality")

        if efficiency_score >= 0.7:
            strengths.append("execution_efficiency")
        elif efficiency_score < 0.4:
            weaknesses.append("execution_efficiency")

        if overall_score >= 0.75:
            status = EvaluationStatus.ACCEPTED
        elif overall_score >= 0.45:
            status = EvaluationStatus.REVIEW
        else:
            status = EvaluationStatus.REJECTED

        return Evaluation(
            experience_id=str(
                experience.experience_id
            ),
            overall_score=overall_score,
            status=status,
            scores=scores,
            strengths=tuple(strengths),
            weaknesses=tuple(weaknesses),
            rationale=(
                "Evaluation is derived from measurable success, "
                "reward, and execution-efficiency signals."
            ),
        )

    def evaluate_batch(
        self,
        experiences: Iterable[Experience],
    ) -> tuple[Evaluation, ...]:
        """Evaluate a sequence of experiences."""

        return tuple(
            self.evaluate(experience)
            for experience in experiences
        )
