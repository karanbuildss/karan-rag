import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, override_settings

from rag.providers import PineconeVectorStoreProvider, get_vector_store_provider
from rag.types import DocumentChunkPayload


class FakeEmbeddings:
    def embed_documents(self, texts):
        return [[float(index), 0.5] for index, _text in enumerate(texts, start=1)]

    def embed_query(self, text):
        return [0.25, float(len(text))]


class PineconeProviderTests(SimpleTestCase):
    def provider(self):
        index = Mock()
        client = Mock()
        client.Index.return_value = index
        module = SimpleNamespace(Pinecone=Mock(return_value=client))
        patcher = patch.dict(sys.modules, {"pinecone": module})
        patcher.start()
        self.addCleanup(patcher.stop)
        provider = PineconeVectorStoreProvider(
            api_key="test-key",
            index_name="test-index",
            namespace="test-namespace",
            embeddings=FakeEmbeddings(),
        )
        return provider, index

    def test_upsert_query_and_filtered_delete_preserve_metadata(self):
        provider, index = self.provider()
        provider.upsert(
            [
                DocumentChunkPayload(
                    id="chunk-1",
                    text="Reviewed evidence",
                    metadata={"project_id": "project-1", "page": 4},
                )
            ]
        )
        record = index.upsert.call_args.kwargs["vectors"][0]
        self.assertEqual(record["metadata"]["chunk_text"], "Reviewed evidence")
        self.assertEqual(index.upsert.call_args.kwargs["namespace"], "test-namespace")

        index.query.return_value = {
            "matches": [{"id": "chunk-1", "score": 0.91, "metadata": record["metadata"]}]
        }
        result = provider.query("payment", top_k=3, filters={"project_id": "project-1"})[0]
        self.assertEqual(result.text, "Reviewed evidence")
        self.assertEqual(result.metadata["page"], 4)
        self.assertNotIn("chunk_text", result.metadata)

        provider.delete_project("project-1")
        index.delete.assert_called_with(
            filter={"project_id": "project-1"},
            namespace="test-namespace",
        )

    @override_settings(VECTOR_DB_PROVIDER="pinecone", PINECONE_API_KEY="")
    @patch("rag.providers.ChromaVectorStoreProvider")
    def test_missing_pinecone_configuration_falls_back_to_chroma(self, chroma):
        self.assertEqual(get_vector_store_provider(), chroma.return_value)
