"""Deterministic in-memory knowledge index for FACTRON."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping
from uuid import UUID, uuid4

from .process import KnowledgeDocument


@dataclass(frozen=True, slots=True)
class KnowledgeRecord:
    """Immutable indexed knowledge chunk."""

    record_id: UUID = field(default_factory=uuid4)
    document_id: UUID = field(default_factory=uuid4)
    source_id: str = ""
    chunk_index: int = 0
    text: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source_id.strip():
            raise ValueError(
                "source_id cannot be empty"
            )

        if self.chunk_index < 0:
            raise ValueError(
                "chunk_index cannot be negative"
            )

        if not self.text.strip():
            raise ValueError(
                "record text cannot be empty"
            )

        object.__setattr__(
            self,
            "metadata",
            dict(self.metadata),
        )


class KnowledgeIndex:
    """Thread-safe-by-design logical index abstraction.

    The current implementation is deterministic and in-memory.
    Persistent/vector backends can later implement the same boundary.
    """

    def __init__(self) -> None:
        self._records: dict[UUID, KnowledgeRecord] = {}
        self._document_records: dict[
            UUID,
            tuple[UUID, ...],
        ] = {}

    @property
    def size(self) -> int:
        """Return the number of indexed records."""
        return len(self._records)

    def add_document(
        self,
        document: KnowledgeDocument,
    ) -> tuple[KnowledgeRecord, ...]:
        """Index every chunk of a document."""
        if not isinstance(document, KnowledgeDocument):
            raise TypeError(
                "document must be a KnowledgeDocument"
            )

        records: list[KnowledgeRecord] = []

        for index, chunk in enumerate(document.chunks):
            record = KnowledgeRecord(
                document_id=document.document_id,
                source_id=document.source_id,
                chunk_index=index,
                text=chunk,
                metadata=document.metadata,
            )

            self._records[record.record_id] = record
            records.append(record)

        record_ids = tuple(
            record.record_id for record in records
        )

        self._document_records[
            document.document_id
        ] = record_ids

        return tuple(records)

    def get(
        self,
        record_id: UUID,
    ) -> KnowledgeRecord | None:
        """Retrieve one indexed record."""
        if not isinstance(record_id, UUID):
            raise TypeError(
                "record_id must be a UUID"
            )

        return self._records.get(record_id)

    def records_for_document(
        self,
        document_id: UUID,
    ) -> tuple[KnowledgeRecord, ...]:
        """Return records belonging to one document."""
        if not isinstance(document_id, UUID):
            raise TypeError(
                "document_id must be a UUID"
            )

        ids = self._document_records.get(
            document_id,
            (),
        )

        return tuple(
            self._records[record_id]
            for record_id in ids
            if record_id in self._records
        )

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> tuple[KnowledgeRecord, ...]:
        """Perform deterministic lexical relevance search."""
        normalized_query = query.strip().lower()

        if not normalized_query:
            raise ValueError(
                "query cannot be empty"
            )

        if limit <= 0:
            raise ValueError(
                "limit must be greater than zero"
            )

        terms = tuple(
            term
            for term in normalized_query.split()
            if term
        )

        scored: list[
            tuple[int, int, KnowledgeRecord]
        ] = []

        for record in self._records.values():
            text = record.text.lower()

            score = sum(
                text.count(term)
                for term in terms
            )

            if score > 0:
                scored.append(
                    (
                        score,
                        -record.chunk_index,
                        record,
                    )
                )

        scored.sort(
            key=lambda item: (
                -item[0],
                -item[1],
                str(item[2].record_id),
            )
        )

        return tuple(
            item[2]
            for item in scored[:limit]
        )

    def clear(self) -> None:
        """Remove all indexed records."""
        self._records.clear()
        self._document_records.clear()
