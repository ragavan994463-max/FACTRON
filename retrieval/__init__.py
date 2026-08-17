"""FACTRON Omega retrieval subsystem.

Retrieval is intentionally provider-independent.

Pipeline:

    KnowledgeIndex
        ↓
    RetrievalSearcher
        ↓
    RetrievalCandidate
        ↓
    RetrievalReranker
        ↓
    RerankedResult
        ↓
    RetrievalGrounder
        ↓
    GroundedContext

The subsystem performs deterministic lexical retrieval today.
Vector databases, embeddings, and model-specific retrieval can
be introduced behind these contracts later without changing the
public architecture.
"""

from .search import (
    RetrievalCandidate,
    RetrievalQuery,
    RetrievalSearcher,
)
from .rerank import (
    RerankedResult,
    RetrievalReranker,
)
from .grounding import (
    GroundedContext,
    GroundingSource,
    RetrievalGrounder,
)

__all__ = [
    "RetrievalCandidate",
    "RetrievalQuery",
    "RetrievalSearcher",
    "RerankedResult",
    "RetrievalReranker",
    "GroundedContext",
    "GroundingSource",
    "RetrievalGrounder",
]
