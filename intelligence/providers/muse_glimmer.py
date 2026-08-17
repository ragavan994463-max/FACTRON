"""Muse Glimmer provider adapter.

This module defines FACTRON's stable boundary for Muse Glimmer.
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
class MuseGlimmerConfig:
    """Muse Glimmer configuration."""

    model: str = "muse-glimmer"
    enabled: bool = True


class MuseGlimmerProvider(ReasoningProvider):
    """Muse Glimmer provider boundary."""

    name = "muse_glimmer"

    def __init__(
        self,
        config: MuseGlimmerConfig | None = None,
    ) -> None:
        self._config = config or MuseGlimmerConfig()

        if not self._config.model.strip():
            raise ValueError(
                "Muse Glimmer model cannot be empty"
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
        """Generate through the future Muse Glimmer transport.

        The transport is intentionally not fabricated here.
        """
        if not self.enabled:
            raise RuntimeError(
                "Muse Glimmer provider is disabled"
            )

        if not isinstance(request, ReasoningRequest):
            raise TypeError(
                "request must be a ReasoningRequest"
            )

        raise RuntimeError(
            "Muse Glimmer transport is not configured. "
            "Connect the real provider transport before generation."
        )
