"""Qwen provider adapter.

This module defines FACTRON's stable boundary for Qwen.
Network transport is intentionally kept outside the core contract.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..reasoning import (
    ReasoningProvider,
    ReasoningRequest,
    ReasoningResponse,
)


@dataclass(frozen=True, slots=True)
class QwenConfig:
    """Qwen configuration."""

    model: str = "qwen"
    enabled: bool = True


class QwenProvider(ReasoningProvider):
    """Qwen provider boundary."""

    name = "qwen"

    def __init__(
        self,
        config: QwenConfig | None = None,
    ) -> None:
        self._config = config or QwenConfig()

        if not self._config.model.strip():
            raise ValueError(
                "Qwen model cannot be empty"
            )

    @property
    def model(self) -> str:
        """Return configured model identifier."""
        return self._config.model

    @property
    def enabled(self) -> bool:
        """Return provider availability configuration."""
        return self._config.enabled

    def generate(
        self,
        request: ReasoningRequest,
    ) -> ReasoningResponse:
        """Generate through the future Qwen transport.

        The transport is intentionally not fabricated here.
        """
        if not self.enabled:
            raise RuntimeError(
                "Qwen provider is disabled"
            )

        if not isinstance(request, ReasoningRequest):
            raise TypeError(
                "request must be a ReasoningRequest"
            )

        raise RuntimeError(
            "Qwen transport is not configured. "
            "Connect the real provider transport before generation."
        )
