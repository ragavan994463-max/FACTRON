"""FACTRON Omega knowledge subsystem.

The knowledge subsystem is responsible for:
    - source representation
    - ingestion
    - normalization
    - processing
    - deterministic indexing

It does not depend on a particular LLM provider.
"""

from .sources import (
    KnowledgeSource,
    SourceType,
)
from .ingest import (
    IngestionResult,
    KnowledgeIngestor,
)
from .process import (
    KnowledgeDocument,
    KnowledgeProcessor,
)
from .index import (
    KnowledgeIndex,
    KnowledgeRecord,
)

__all__ = [
    "KnowledgeSource",
    "SourceType",
    "IngestionResult",
    "KnowledgeIngestor",
    "KnowledgeDocument",
    "KnowledgeProcessor",
    "KnowledgeIndex",
    "KnowledgeRecord",
]
