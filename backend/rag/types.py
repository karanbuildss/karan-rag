from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class DocumentChunkPayload:
    id: str
    text: str
    metadata: dict
    embedding_text: str | None = None


@dataclass(frozen=True)
class RetrievedChunk:
    id: str
    text: str
    score: float
    metadata: dict


class VectorStoreProvider(Protocol):
    name: str

    def upsert(self, chunks: list[DocumentChunkPayload]) -> None: ...

    def query(
        self,
        text: str,
        *,
        top_k: int,
        filters: dict | None = None,
    ) -> list[RetrievedChunk]: ...

    def delete_document(self, document_id: str) -> None: ...

    def delete_project(self, project_id: str) -> None: ...
