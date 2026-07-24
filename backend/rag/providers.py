from pathlib import Path

from django.conf import settings

from rag.embeddings import OllamaEmbeddingProvider
from rag.types import DocumentChunkPayload, RetrievedChunk


class VectorStoreUnavailable(RuntimeError):
    """Raised when an optional vector provider is not configured or reachable."""


def _clean_metadata(metadata):
    allowed_types = (str, int, float, bool)
    return {
        key: value if isinstance(value, allowed_types) else str(value)
        for key, value in metadata.items()
        if value is not None
    }


def _chroma_where(filters):
    if not filters:
        return None
    clauses = [{key: value} for key, value in filters.items()]
    return clauses[0] if len(clauses) == 1 else {"$and": clauses}


class ChromaVectorStoreProvider:
    name = "chroma"

    def __init__(self, *, path=None, collection_name=None, embeddings=None):
        try:
            import chromadb
        except ImportError as exc:
            raise VectorStoreUnavailable(
                "ChromaDB is not installed. Install backend requirements first."
            ) from exc

        store_path = Path(path or settings.CHROMA_DB_DIR)
        store_path.mkdir(parents=True, exist_ok=True)
        self.embeddings = embeddings or OllamaEmbeddingProvider()
        self.client = chromadb.PersistentClient(path=str(store_path))
        self.collection = self.client.get_or_create_collection(
            name=collection_name or settings.CHROMA_COLLECTION,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert(self, chunks: list[DocumentChunkPayload]) -> None:
        if not chunks:
            return
        vectors = self.embeddings.embed_documents(
            [chunk.embedding_text or chunk.text for chunk in chunks]
        )
        self.collection.upsert(
            ids=[chunk.id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            embeddings=vectors,
            metadatas=[_clean_metadata(chunk.metadata) for chunk in chunks],
        )

    def query(self, text, *, top_k, filters=None):
        query_vector = self.embeddings.embed_query(text)
        result = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=_chroma_where(filters),
            include=["documents", "metadatas", "distances"],
        )
        ids = (result.get("ids") or [[]])[0]
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        return [
            RetrievedChunk(
                id=chunk_id,
                text=document or "",
                score=max(0.0, 1.0 - float(distance)),
                metadata=metadata or {},
            )
            for chunk_id, document, metadata, distance in zip(
                ids,
                documents,
                metadatas,
                distances,
                strict=True,
            )
        ]

    def delete_document(self, document_id):
        self.collection.delete(where={"document_id": str(document_id)})

    def delete_project(self, project_id):
        self.collection.delete(where={"project_id": str(project_id)})


def get_vector_store_provider():
    provider = settings.VECTOR_DB_PROVIDER.lower()
    if provider == "chroma":
        return ChromaVectorStoreProvider()
    if provider == "pinecone":
        raise VectorStoreUnavailable(
            "Pinecone is not enabled in Phase 3A; use VECTOR_DB_PROVIDER=chroma."
        )
    raise VectorStoreUnavailable(f"Unsupported vector provider: {provider}")
