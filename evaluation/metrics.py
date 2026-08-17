"""Deterministic evaluation metrics for FACTRON.

This module contains provider-independent mathematical metrics.
It intentionally uses only the Python standard library.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable, Sequence


def _validate_probability(value: float, name: str) -> float:
    """Validate a normalized score in the inclusive [0, 1] range."""
    value = float(value)

    if not isfinite(value):
        raise ValueError(f"{name} must be finite.")

    if value < 0.0 or value > 1.0:
        raise ValueError(f"{name} must be between 0.0 and 1.0.")

    return value


def _validate_positive(value: float, name: str) -> float:
    """Validate a strictly positive finite number."""
    value = float(value)

    if not isfinite(value):
        raise ValueError(f"{name} must be finite.")

    if value <= 0.0:
        raise ValueError(f"{name} must be greater than zero.")

    return value


@dataclass(frozen=True, slots=True)
class MetricResult:
    """Immutable result produced by an evaluation metric."""

    name: str
    value: float
    sample_count: int

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Metric name cannot be empty.")

        if self.sample_count < 0:
            raise ValueError("sample_count cannot be negative.")

        object.__setattr__(self, "value", _validate_probability(self.value, "value"))

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""
        return {
            "name": self.name,
            "value": self.value,
            "sample_count": self.sample_count,
        }


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    """Immutable collection of evaluation metrics."""

    metrics: tuple[MetricResult, ...]
    score: float

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "score",
            _validate_probability(self.score, "score"),
        )

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-compatible representation."""
        return {
            "score": self.score,
            "metrics": [metric.as_dict() for metric in self.metrics],
        }


def accuracy(
    expected: Sequence[object],
    actual: Sequence[object],
) -> MetricResult:
    """Calculate exact-match accuracy.

    Returns a normalized value between 0 and 1.
    """
    expected_values = tuple(expected)
    actual_values = tuple(actual)

    if len(expected_values) != len(actual_values):
        raise ValueError(
            "expected and actual must contain the same number of items."
        )

    count = len(expected_values)

    if count == 0:
        return MetricResult("accuracy", 0.0, 0)

    correct = sum(
        1 for expected_value, actual_value
        in zip(expected_values, actual_values)
        if expected_value == actual_value
    )

    return MetricResult("accuracy", correct / count, count)


def success_rate(results: Iterable[bool]) -> MetricResult:
    """Calculate the fraction of successful evaluation cases."""
    values = tuple(bool(result) for result in results)
    count = len(values)

    if count == 0:
        return MetricResult("success_rate", 0.0, 0)

    successes = sum(values)

    return MetricResult("success_rate", successes / count, count)


def latency_score(
    latency_seconds: float,
    target_seconds: float,
) -> MetricResult:
    """Convert latency into a normalized performance score.

    A result at or below the target receives 1.0.
    Slower results receive a smoothly decreasing score.
    """
    latency = _validate_positive(latency_seconds, "latency_seconds")
    target = _validate_positive(target_seconds, "target_seconds")

    score = min(1.0, target / latency)

    return MetricResult("latency_score", score, 1)


def composite_score(
    metrics: Iterable[MetricResult],
    weights: Iterable[float] | None = None,
) -> float:
    """Calculate a weighted normalized evaluation score."""
    metric_values = tuple(metrics)

    if not metric_values:
        return 0.0

    if weights is None:
        normalized_weights = tuple(1.0 for _ in metric_values)
    else:
        normalized_weights = tuple(float(weight) for weight in weights)

        if len(normalized_weights) != len(metric_values):
            raise ValueError(
                "weights must have the same length as metrics."
            )

        for weight in normalized_weights:
            if not isfinite(weight) or weight < 0.0:
                raise ValueError(
                    "weights must be finite and non-negative."
                )

    total_weight = sum(normalized_weights)

    if total_weight <= 0.0:
        raise ValueError("At least one weight must be greater than zero.")

    weighted_sum = sum(
        metric.value * weight
        for metric, weight in zip(metric_values, normalized_weights)
    )

    return _validate_probability(
        weighted_sum / total_weight,
        "composite_score",
    )


def build_report(
    metrics: Iterable[MetricResult],
    weights: Iterable[float] | None = None,
) -> EvaluationReport:
    """Build an immutable evaluation report."""
    metric_tuple = tuple(metrics)

    return EvaluationReport(
        metrics=metric_tuple,
        score=composite_score(metric_tuple, weights),
    )
