from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from rag.embeddings import OllamaEmbeddingProvider
from rag.search import expanded_query_text, rank_lexical, search_tokens
from rag.types import DocumentChunkPayload


class MultilingualSearchTests(SimpleTestCase):
    def test_query_normalization_expands_romanized_nepali_and_digits(self):
        tokens = search_tokens("Wada ८ ko bhuktani kati cha?", expand=True)

        self.assertIn("ward", tokens)
        self.assertIn("payment", tokens)
        self.assertIn("8", tokens)

    def test_light_english_lemmatization_keeps_matching_financial_terms(self):
        tokens = search_tokens("allocated payments documents")

        self.assertEqual(tokens, ["allocation", "payment", "document"])

    def test_exact_contract_identifier_dominates_bm25_ranking(self):
        payloads = [
            DocumentChunkPayload(
                id="allocation",
                text="Jalpa Marg budget allocation NPR 800000",
                metadata={"relationship": "allocation"},
            ),
            DocumentChunkPayload(
                id="tender",
                text=("Official tender Contract ID 45/PMC/NCB/W/077-78 with invitation for bids"),
                metadata={"relationship": "procurement"},
            ),
        ]

        results = rank_lexical("show 45/PMC/NCB/W/077-78", payloads)

        self.assertEqual(results[0].id, "tender")
        self.assertGreater(results[0].score, 8)

    def test_embedding_query_keeps_original_text_and_adds_search_aliases(self):
        expanded = expanded_query_text("jalpa ko thekka kati ho?")

        self.assertIn("jalpa ko thekka kati ho?", expanded)
        self.assertIn("tender", expanded)
        self.assertIn("contract", expanded)


class NomicEmbeddingPrefixTests(SimpleTestCase):
    @override_settings(
        OLLAMA_EMBEDDING_DOCUMENT_PREFIX="search_document:",
        OLLAMA_EMBEDDING_QUERY_PREFIX="search_query:",
    )
    def test_uses_asymmetric_document_and_query_prefixes(self):
        provider = OllamaEmbeddingProvider(
            base_url="http://localhost:11434",
            model="test-model",
            timeout=1,
        )
        with patch.object(provider, "embed", side_effect=[[[1.0]], [[2.0]]]) as embed:
            documents = provider.embed_documents(["official evidence"])
            query = provider.embed_query("where did money go")

        self.assertEqual(documents, [[1.0]])
        self.assertEqual(query, [2.0])
        self.assertEqual(
            embed.call_args_list[0].args[0],
            ["search_document: official evidence"],
        )
        self.assertEqual(
            embed.call_args_list[1].args[0],
            ["search_query: where did money go"],
        )
