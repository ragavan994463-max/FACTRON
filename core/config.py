"""FACTRON configuration contracts.

Configuration is represented as immutable typed objects rather than scattered
environment lookups. Environment integration can be layered on top later.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ModelConfig:
    """Configuration for a model provider."""

    provider: str = "muse_glimmer"
    model_name: str = "muse-glimmer"
    temperature: float = 0.2
    max_tokens: int = 4096

    def __post_init__(self) -> None:
        if not self.provider.strip():
            raise ValueError("Model provider cannot be empty.")
        if not self.model_name.strip():
            raise ValueError("Model name cannot be empty.")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0.")
        if self.max_tokens <= 0:
            raise ValueError("max_tokens must be greater than zero.")


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    """Runtime limits and execution settings."""

    environment: str = "development"
    max_agent_steps: int = 32
    request_timeout_seconds: float = 120.0
    debug: bool = True

    def __post_init__(self) -> None:
        if not self.environment.strip():
            raise ValueError("Environment cannot be empty.")
        if self.max_agent_steps <= 0:
            raise ValueError("max_agent_steps must be greater than zero.")
        if self.request_timeout_seconds <= 0:
            raise ValueError("Request timeout must be positive.")


@dataclass(frozen=True, slots=True)
class FactronConfig:
    """Complete immutable FACTRON configuration."""

    root_dir: Path
    model: ModelConfig = field(default_factory=ModelConfig)
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)

    @property
    def data_dir(self) -> Path:
        """Return the persistent data directory."""
        return self.root_dir / "data"

    @property
    def raw_data_dir(self) -> Path:
        """Return the raw knowledge directory."""
        return self.data_dir / "raw"

    @property
    def processed_data_dir(self) -> Path:
        """Return processed knowledge storage."""
        return self.data_dir / "processed"

    @property
    def memory_dir(self) -> Path:
        """Return persistent memory storage."""
        return self.data_dir / "memory"

    def ensure_directories(self) -> None:
        """Create required runtime directories."""
        for directory in (
            self.data_dir,
            self.raw_data_dir,
            self.processed_data_dir,
            self.memory_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_root(cls, root_dir: str | Path) -> "FactronConfig":
        """Create configuration from a project root."""
        return cls(root_dir=Path(root_dir).resolve())
