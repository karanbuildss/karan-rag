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


class PineconeVectorStoreProvider:
    """Pinecone adapter using the same local Ollama embedding space as Chroma."""

    name = "pinecone"

    def __init__(self, *, api_key=None, index_name=None, namespace=None, embeddings=None):
        key = api_key or settings.PINECONE_API_KEY
        if not key:
            raise VectorStoreUnavailable("PINECONE_API_KEY is not configured.")
        try:
            from pinecone import Pinecone
        except ImportError as exc:
            raise VectorStoreUnavailable(
                "The Pinecone SDK is not installed. Install backend requirements first."
            ) from exc
        try:
            self.client = Pinecone(api_key=key)
            self.index = self.client.Index(index_name or settings.PINECONE_INDEX)
        except Exception as exc:
            raise VectorStoreUnavailable("The configured Pinecone index is unavailable.") from exc
        self.namespace = namespace or settings.PINECONE_NAMESPACE
        self.embeddings = embeddings or OllamaEmbeddingProvider()

    def upsert(self, chunks: list[DocumentChunkPayload]) -> None:
        if not chunks:
            return
        vectors = self.embeddings.embed_documents(
            [chunk.embedding_text or chunk.text for chunk in chunks]
        )
        records = []
        for chunk, vector in zip(chunks, vectors, strict=True):
            metadata = _clean_metadata(chunk.metadata)
            metadata["chunk_text"] = chunk.text
            records.append({"id": chunk.id, "values": vector, "metadata": metadata})
        self.index.upsert(vectors=records, namespace=self.namespace)

    def query(self, text, *, top_k, filters=None):
        response = self.index.query(
            vector=self.embeddings.embed_query(text),
            top_k=top_k,
            filter=filters or None,
            namespace=self.namespace,
            include_metadata=True,
            include_values=False,
        )
        matches = response.get("matches", []) if isinstance(response, dict) else response.matches
        results = []
        for match in matches:
            if isinstance(match, dict):
                chunk_id = match["id"]
                score = match.get("score", 0)
                metadata = dict(match.get("metadata") or {})
            else:
                chunk_id = match.id
                score = match.score
                metadata = dict(match.metadata or {})
            chunk_text = metadata.pop("chunk_text", "")
            results.append(
                RetrievedChunk(
                    id=chunk_id,
                    text=chunk_text,
                    score=float(score),
                    metadata=metadata,
                )
            )
        return results

    def delete_document(self, document_id):
        self.index.delete(
            filter={"document_id": str(document_id)},
            namespace=self.namespace,
        )

    def delete_project(self, project_id):
        self.index.delete(
            filter={"project_id": str(project_id)},
            namespace=self.namespace,
        )


def get_vector_store_provider():
    provider = settings.VECTOR_DB_PROVIDER.lower()
    if provider == "chroma":
        return ChromaVectorStoreProvider()
    if provider == "pinecone":
        try:
            return PineconeVectorStoreProvider()
        except VectorStoreUnavailable:
            if settings.PINECONE_FALLBACK_TO_CHROMA:
                return ChromaVectorStoreProvider()
            raise
    raise VectorStoreUnavailable(f"Unsupported vector provider: {provider}")
