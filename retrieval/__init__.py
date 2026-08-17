"""FACTRON Omega retrieval subsystem.

Retrieval converts a user/query signal into relevant knowledge records.

Architecture:

    Query
      |
      v
    Search
      |
      v
    Candidate Records
      |
      v
    Reranking
      |
      v
    Grounding
      |
      v
    Retrieval Context

The subsystem is provider-independent and deterministic.

No LLM, embedding API, vector database, network service, or external
credential is required by the core retrieval contracts.
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
