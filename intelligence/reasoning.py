"""Provider-independent reasoning contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol


@dataclass(frozen=True, slots=True)
class ReasoningRequest:
    """Immutable request sent to an intelligence provider."""

    prompt: str
    system_prompt: str = ""
    context: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        prompt = self.prompt.strip()

        if not prompt:
            raise ValueError("prompt cannot be empty")

        object.__setattr__(self, "prompt", prompt)
        object.__setattr__(
            self,
            "system_prompt",
            self.system_prompt.strip(),
        )
        object.__setattr__(
            self,
            "context",
            tuple(str(item) for item in self.context),
        )
        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )


@dataclass(frozen=True, slots=True)
class ReasoningResponse:
    """Normalized immutable provider response."""

    text: str
    provider: str
    model: str
    latency_seconds: float = 0.0
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        text = self.text.strip()
        provider = self.provider.strip()
        model = self.model.strip()

        if not text:
            raise ValueError("text cannot be empty")

        if not provider:
            raise ValueError("provider cannot be empty")

        if not model:
            raise ValueError("model cannot be empty")

        if self.latency_seconds < 0:
            raise ValueError("latency_seconds cannot be negative")

        object.__setattr__(self, "text", text)
        object.__setattr__(self, "provider", provider)
        object.__setattr__(self, "model", model)
        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )

    def as_dict(self) -> dict[str, Any]:
        """Return a serializable representation."""
        return {
            "text": self.text,
            "provider": self.provider,
            "model": self.model,
            "latency_seconds": self.latency_seconds,
            "metadata": dict(self.metadata),
        }


class ReasoningProvider(Protocol):
    """Structural interface required from every provider."""

    @property
    def name(self) -> str:
        ...

    @property
    def model(self) -> str:
        ...

    def generate(
        self,
        request: ReasoningRequest,
    ) -> ReasoningResponse:
        ...


class ReasoningEngine:
    """Provider-independent reasoning facade."""

    def __init__(self, provider: ReasoningProvider) -> None:
        if provider is None:
            raise ValueError("provider cannot be None")

        self._provider = provider

    @property
    def provider(self) -> ReasoningProvider:
        """Return the active provider."""
        return self._provider

    def generate(
        self,
        request: ReasoningRequest,
    ) -> ReasoningResponse:
        """Generate a response through the active provider."""
        if not isinstance(request, ReasoningRequest):
            raise TypeError(
                "request must be a ReasoningRequest"
            )

        response = self._provider.generate(request)

        if not isinstance(response, ReasoningResponse):
            raise TypeError(
                "provider must return ReasoningResponse"
            )

        return response
