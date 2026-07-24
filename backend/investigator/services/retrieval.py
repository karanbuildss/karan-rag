from django.conf import settings
from documents.models import ProjectDocumentLink
from rag.evidence import project_evidence_payloads
from rag.providers import VectorStoreUnavailable, get_vector_store_provider
from rag.search import expanded_query_text, preferred_relationships, rank_lexical

from investigator.services.routing import InvestigationRoute, QuestionLanguage

RELATIONSHIP_ORDER = {
    ProjectDocumentLink.Relationship.ALLOCATION: 0,
    ProjectDocumentLink.Relationship.PROCUREMENT: 1,
    ProjectDocumentLink.Relationship.AUDIT: 2,
    ProjectDocumentLink.Relationship.PAYMENT: 3,
    ProjectDocumentLink.Relationship.PROGRESS: 4,
    ProjectDocumentLink.Relationship.COMPLETION: 5,
    ProjectDocumentLink.Relationship.CONTEXT: 6,
}


def _fused_results(payloads, lexical_results, vector_results, relationship_preferences):
    payload_by_id = {payload.id: payload for payload in payloads}
    scores = {payload.id: 0.0 for payload in payloads}
    for rank, result in enumerate(vector_results, start=1):
        if result.id in scores:
            scores[result.id] += 1.0 / (50 + rank)
    for rank, result in enumerate(lexical_results, start=1):
        if result.id in scores:
            scores[result.id] += 1.15 / (50 + rank)
            scores[result.id] += min(result.score, 12.0) / 1000
    for payload in payloads:
        if payload.metadata.get("relationship") in relationship_preferences:
            scores[payload.id] += 0.08
    return sorted(
        payload_by_id.values(),
        key=lambda payload: (
            -scores[payload.id],
            RELATIONSHIP_ORDER.get(payload.metadata.get("relationship"), 9),
            payload.id,
        ),
    )


def _select_payloads(ranked, *, route, top_k):
    selected = []
    selected_ids = set()
    if route == InvestigationRoute.PROJECT_INVESTIGATION:
        for relationship in (
            ProjectDocumentLink.Relationship.ALLOCATION,
            ProjectDocumentLink.Relationship.PROCUREMENT,
            ProjectDocumentLink.Relationship.AUDIT,
        ):
            candidate = next(
                (
                    payload
                    for payload in ranked
                    if payload.metadata.get("relationship") == relationship
                ),
                None,
            )
            if candidate:
                selected.append(candidate)
                selected_ids.add(candidate.id)
    for payload in ranked:
        if len(selected) >= top_k:
            break
        if payload.id not in selected_ids:
            selected.append(payload)
            selected_ids.add(payload.id)
    return selected


def _citation(payload, link, language):
    metadata = payload.metadata
    evidence_note = (
        link.evidence_note_np
        if language == QuestionLanguage.NEPALI and link.evidence_note_np
        else link.evidence_note_en
    )
    source_kind = metadata.get("source_kind", "curated_project_evidence")
    excerpt = payload.text if source_kind == "reviewed_document_page" else evidence_note
    page = metadata.get("page") or link.page_from
    return {
        "document_id": str(link.document_id),
        "document_title": link.document.title_en,
        "document_title_np": link.document.title_np,
        "page": page,
        "page_to": metadata.get("page_to") or link.page_to,
        "section": metadata.get("section") or link.section,
        "source_url": link.document.source_url,
        "relationship": link.relationship,
        "evidence_note": evidence_note,
        "excerpt": excerpt[:1600],
        "source_kind": source_kind,
        "review_status": metadata.get("review_status"),
        "viewer_path": f"/documents/{link.document_id}?page={page or 1}",
    }


def retrieve_project_evidence(project, question, route, language):
    links = list(
        ProjectDocumentLink.objects.filter(project=project).select_related(
            "document",
            "document__local_government",
            "document__fiscal_year",
        )
    )
    if not links:
        return [], "bm25_evidence"
    links_by_id = {link.id: link for link in links}
    payloads = project_evidence_payloads(project)
    candidate_count = min(max(settings.INVESTIGATOR_TOP_K * 3, 10), len(payloads))
    lexical_results = rank_lexical(question, payloads, top_k=candidate_count)
    vector_results = []
    provider_name = "bm25_evidence"
    if settings.VECTOR_DB_PROVIDER.lower() in {"chroma", "pinecone"}:
        try:
            provider = get_vector_store_provider()
            vector_results = provider.query(
                expanded_query_text(question),
                top_k=candidate_count,
                filters={"project_id": str(project.id)},
            )
            if vector_results:
                provider_name = f"hybrid_{provider.name}_bm25"
        except (VectorStoreUnavailable, ValueError, TypeError, KeyError, RuntimeError, OSError):
            provider_name = "bm25_evidence"

    ranked = _fused_results(
        payloads,
        lexical_results,
        vector_results,
        preferred_relationships(question),
    )
    selected = _select_payloads(
        ranked,
        route=route,
        top_k=settings.INVESTIGATOR_TOP_K,
    )
    citations = []
    seen_citations = set()
    for payload in selected:
        link_id = payload.metadata.get("link_id")
        try:
            link = links_by_id[int(link_id)]
        except (KeyError, TypeError, ValueError):
            continue
        citation = _citation(payload, link, language)
        citation_key = (
            citation["document_id"],
            citation["page"],
            citation["section"],
            citation["source_kind"],
        )
        if citation_key not in seen_citations:
            citations.append(citation)
            seen_citations.add(citation_key)
    return citations, provider_name
