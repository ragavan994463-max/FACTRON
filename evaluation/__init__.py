"""FACTRON evaluation subsystem.

Provides deterministic metrics and benchmark primitives for measuring
system behavior without coupling evaluation to a specific model provider.
"""

from .metrics import (
    MetricResult,
    EvaluationReport,
    accuracy,
    success_rate,
    latency_score,
    composite_score,
)

from .benchmarks import (
    BenchmarkCase,
    BenchmarkResult,
    BenchmarkSuite,
    run_benchmark,
)

__all__ = [
    "MetricResult",
    "EvaluationReport",
    "accuracy",
    "success_rate",
    "latency_score",
    "composite_score",
    "BenchmarkCase",
    "BenchmarkResult",
    "BenchmarkSuite",
    "run_benchmark",
]
