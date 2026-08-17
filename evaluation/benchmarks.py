"""Provider-independent benchmark execution for FACTRON."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Callable, Iterable, Mapping


BenchmarkFunction = Callable[[Any], Any]


@dataclass(frozen=True, slots=True)
class BenchmarkCase:
    """A single deterministic benchmark case."""

    name: str
    input_data: Any
    expected_output: Any

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Benchmark case name cannot be empty.")


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Immutable result for one benchmark case."""

    name: str
    passed: bool
    elapsed_seconds: float
    actual_output: Any
    expected_output: Any

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Benchmark result name cannot be empty.")

        if self.elapsed_seconds < 0.0:
            raise ValueError("elapsed_seconds cannot be negative.")

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return {
            "name": self.name,
            "passed": self.passed,
            "elapsed_seconds": self.elapsed_seconds,
            "actual_output": self.actual_output,
            "expected_output": self.expected_output,
        }


@dataclass(frozen=True, slots=True)
class BenchmarkSuite:
    """Immutable collection of benchmark results."""

    name: str
    results: tuple[BenchmarkResult, ...]

    @property
    def total(self) -> int:
        """Return the number of executed cases."""
        return len(self.results)

    @property
    def passed(self) -> int:
        """Return the number of successful cases."""
        return sum(result.passed for result in self.results)

    @property
    def failed(self) -> int:
        """Return the number of failed cases."""
        return self.total - self.passed

    @property
    def success_rate(self) -> float:
        """Return normalized benchmark success."""
        if self.total == 0:
            return 0.0

        return self.passed / self.total

    @property
    def total_elapsed_seconds(self) -> float:
        """Return total measured execution time."""
        return sum(result.elapsed_seconds for result in self.results)

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return {
            "name": self.name,
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "success_rate": self.success_rate,
            "total_elapsed_seconds": self.total_elapsed_seconds,
            "results": [result.as_dict() for result in self.results],
        }


def run_benchmark(
    name: str,
    cases: Iterable[BenchmarkCase],
    function: BenchmarkFunction,
) -> BenchmarkSuite:
    """Execute benchmark cases and collect deterministic results.

    Exceptions raised by a benchmark function are converted into failed
    benchmark results so that one faulty case does not prevent the suite
    from measuring remaining cases.
    """
    if not name.strip():
        raise ValueError("Benchmark suite name cannot be empty.")

    if not callable(function):
        raise TypeError("function must be callable.")

    results: list[BenchmarkResult] = []

    for case in tuple(cases):
        started = perf_counter()

        try:
            actual = function(case.input_data)
            passed = actual == case.expected_output
        except Exception as exc:
            actual = f"{type(exc).__name__}: {exc}"
            passed = False

        elapsed = perf_counter() - started

        results.append(
            BenchmarkResult(
                name=case.name,
                passed=passed,
                elapsed_seconds=elapsed,
                actual_output=actual,
                expected_output=case.expected_output,
            )
        )

    return BenchmarkSuite(
        name=name,
        results=tuple(results),
    )
