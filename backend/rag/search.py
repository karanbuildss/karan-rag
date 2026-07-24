import math
import re
import unicodedata
from collections import Counter

from rag.types import RetrievedChunk

NEPALI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
TOKEN_PATTERN = re.compile(
    r"[a-z0-9]+(?:[./-][a-z0-9]+)+|[a-z]+|[\u0900-\u097f]+|\d+(?:[.,]\d+)*",
    re.IGNORECASE,
)
IRREGULAR_ENGLISH_LEMMAS = {
    "allocations": "allocation",
    "allocated": "allocation",
    "awarded": "award",
    "awards": "award",
    "documents": "document",
    "paid": "payment",
    "payments": "payment",
    "spent": "spend",
    "went": "go",
}
QUERY_EXPANSIONS = {
    "anugaman": ("monitoring", "progress", "अनुगमन"),
    "bajet": ("budget", "बजेट"),
    "bhuktani": ("payment", "paid", "भुक्तानी"),
    "gayo": ("go", "spend", "खर्च"),
    "kaha": ("where", "कहाँ"),
    "kata": ("where", "कता"),
    "kharcha": ("spend", "payment", "खर्च"),
    "lekha": ("audit", "लेखापरीक्षण"),
    "miti": ("date", "मिति"),
    "paisa": ("money", "payment", "spend", "पैसा", "रकम"),
    "pragati": ("progress", "completion", "प्रगति"),
    "samjhauta": ("agreement", "contract", "सम्झौता"),
    "thekka": ("tender", "contract", "award", "ठेक्का", "बोलपत्र"),
    "wada": ("ward", "वडा"),
    "yojana": ("project", "आयोजना"),
    "भुक्तानी": ("payment", "paid", "bhuktani"),
    "बजेट": ("budget", "allocation"),
    "बोलपत्र": ("tender", "procurement", "thekka"),
    "पेश्की": ("advance", "audit"),
    "लेखापरीक्षण": ("audit", "report"),
    "विनियोजन": ("allocation", "budget"),
}
RELATIONSHIP_SEARCH_TERMS = {
    "allocation": {"allocation", "budget", "विनियोजन", "बजेट"},
    "procurement": {
        "award",
        "bolpatra",
        "contract",
        "procurement",
        "tender",
        "ठेक्का",
        "बोलपत्र",
    },
    "audit": {"advance", "audit", "report", "पेश्की", "लेखापरीक्षण", "प्रतिवेदन"},
    "payment": {"money", "paid", "payment", "spend", "खर्च", "भुक्तानी", "पैसा", "रकम"},
    "progress": {
        "agreement",
        "anugaman",
        "completion",
        "date",
        "milestone",
        "monitoring",
        "pragati",
        "progress",
        "samjhauta",
        "अनुगमन",
        "प्रगति",
        "मिति",
        "सम्झौता",
        "सम्पन्न",
    },
}


def normalize_digits(text):
    return unicodedata.normalize("NFC", text or "").translate(NEPALI_DIGITS)


def light_english_lemma(token):
    if token in IRREGULAR_ENGLISH_LEMMAS:
        return IRREGULAR_ENGLISH_LEMMAS[token]
    if len(token) > 5 and token.endswith("ies"):
        return f"{token[:-3]}y"
    if len(token) > 5 and token.endswith("ing"):
        root = token[:-3]
        if len(root) > 2 and root[-1] == root[-2]:
            root = root[:-1]
        return root
    if len(token) > 4 and token.endswith("ed"):
        return token[:-2]
    if len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def search_tokens(text, *, expand=False):
    normalized = normalize_digits(text).casefold()
    raw_tokens = TOKEN_PATTERN.findall(normalized)
    tokens = []
    for token in raw_tokens:
        lemma = light_english_lemma(token) if token.isascii() and token.isalpha() else token
        tokens.append(lemma)
        if expand:
            for expansion in QUERY_EXPANSIONS.get(token, ()):
                expanded = expansion.casefold()
                tokens.append(
                    light_english_lemma(expanded)
                    if expanded.isascii() and expanded.isalpha()
                    else expanded
                )
    return tokens


def expanded_query_text(text):
    tokens = search_tokens(text, expand=True)
    return f"{normalize_digits(text).strip()}\nSearch aliases: {' '.join(tokens)}"


def preferred_relationships(text):
    tokens = set(search_tokens(text, expand=True))
    return {
        relationship for relationship, terms in RELATIONSHIP_SEARCH_TERMS.items() if tokens & terms
    }


def rank_lexical(query, payloads, *, top_k=None):
    if not payloads:
        return []
    query_tokens = search_tokens(query, expand=True)
    if not query_tokens:
        return []
    document_tokens = [
        search_tokens(payload.embedding_text or payload.text) for payload in payloads
    ]
    document_frequencies = Counter()
    for tokens in document_tokens:
        document_frequencies.update(set(tokens))
    average_length = sum(len(tokens) for tokens in document_tokens) / len(document_tokens)
    query_counts = Counter(query_tokens)
    exact_identifiers = {
        token for token in query_tokens if any(character in token for character in "/-.")
    }
    results = []
    for payload, tokens in zip(payloads, document_tokens, strict=True):
        frequencies = Counter(tokens)
        length = len(tokens)
        score = 0.0
        for token, query_frequency in query_counts.items():
            term_frequency = frequencies[token]
            if not term_frequency:
                continue
            inverse_document_frequency = math.log(
                1
                + (len(payloads) - document_frequencies[token] + 0.5)
                / (document_frequencies[token] + 0.5)
            )
            denominator = term_frequency + 1.5 * (1 - 0.75 + 0.75 * length / max(1, average_length))
            score += (
                inverse_document_frequency
                * (term_frequency * 2.5 / denominator)
                * min(query_frequency, 2)
            )
        score += 8.0 * len(exact_identifiers & set(tokens))
        if score > 0:
            results.append(
                RetrievedChunk(
                    id=payload.id,
                    text=payload.text,
                    score=score,
                    metadata=payload.metadata,
                )
            )
    results.sort(key=lambda item: (-item.score, item.id))
    return results[:top_k] if top_k else results
