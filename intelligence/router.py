"""Deterministic intelligence provider router."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .reasoning import (
    ReasoningProvider,
    ReasoningRequest,
    ReasoningResponse,
)


class ProviderUnavailableError(RuntimeError):
    """Raised when a provider cannot be selected."""


@dataclass(frozen=True, slots=True)
class ProviderSelection:
    """Immutable provider selection."""

    provider_name: str
    reason: str


class ProviderRouter:
    """Routes reasoning requests to registered providers."""

    def __init__(
        self,
        providers: Mapping[str, ReasoningProvider],
        default_provider: str,
    ) -> None:
        if not providers:
            raise ValueError(
                "At least one provider is required"
            )

        normalized: dict[str, ReasoningProvider] = {}

        for name, provider in providers.items():
            normalized_name = str(name).strip().lower()

            if not normalized_name:
                raise ValueError(
                    "Provider names cannot be empty"
                )

            if provider is None:
                raise ValueError(
                    f"Provider '{name}' cannot be None"
                )

            normalized[normalized_name] = provider

        default = default_provider.strip().lower()

        if not default:
            raise ValueError(
                "default_provider cannot be empty"
            )

        if default not in normalized:
            raise ProviderUnavailableError(
                f"Default provider '{default_provider}' "
                f"is not registered"
            )

        self._providers = normalized
        self._default_provider = default

    @property
    def default_provider(self) -> str:
        """Return the default provider."""
        return self._default_provider

    @property
    def providers(self) -> tuple[str, ...]:
        """Return registered provider names."""
        return tuple(sorted(self._providers))

    def select(
        self,
        requested: str | None = None,
    ) -> ProviderSelection:
        """Select a provider."""
        if requested is None or not requested.strip():
            return ProviderSelection(
                provider_name=self._default_provider,
                reason="default",
            )

        name = requested.strip().lower()

        if name not in self._providers:
            raise ProviderUnavailableError(
                f"Provider '{requested}' is not registered"
            )

        return ProviderSelection(
            provider_name=name,
            reason="explicit",
        )

    def get(
        self,
        requested: str | None = None,
    ) -> ReasoningProvider:
        """Return the selected provider."""
        selection = self.select(requested)
        return self._providers[selection.provider_name]

    def generate(
        self,
        request: ReasoningRequest,
        provider: str | None = None,
    ) -> ReasoningResponse:
        """Generate through the selected provider."""
        return self.get(provider).generate(request)
