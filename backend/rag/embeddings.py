import json
from urllib import error, request

from django.conf import settings


class EmbeddingUnavailable(RuntimeError):
    """Raised when the configured embedding service cannot return vectors."""


class OllamaEmbeddingProvider:
    def __init__(self, *, base_url=None, model=None, timeout=None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_EMBEDDING_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        payload = json.dumps({"model": self.model, "input": texts}).encode("utf-8")
        http_request = request.Request(
            f"{self.base_url}/api/embed",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except (error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            raise EmbeddingUnavailable("Ollama embeddings are unavailable.") from exc

        embeddings = result.get("embeddings")
        if not isinstance(embeddings, list) or len(embeddings) != len(texts):
            raise EmbeddingUnavailable("Ollama returned an invalid embedding response.")
        return embeddings

    def embed_documents(self, texts):
        prefix = settings.OLLAMA_EMBEDDING_DOCUMENT_PREFIX.strip()
        return self.embed([f"{prefix} {text}" if prefix else text for text in texts])

    def embed_query(self, text):
        prefix = settings.OLLAMA_EMBEDDING_QUERY_PREFIX.strip()
        return self.embed([f"{prefix} {text}" if prefix else text])[0]
