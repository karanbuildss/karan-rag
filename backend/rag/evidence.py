import re
from collections import defaultdict

from django.conf import settings
from documents.models import DocumentChunk, DocumentPage, ProjectDocumentLink
from documents.services import extract_document_pages

from rag.types import DocumentChunkPayload

ACCEPTED_REVIEW_STATUSES = {
    DocumentPage.ReviewStatus.AUTO_ACCEPTED,
    DocumentPage.ReviewStatus.APPROVED,
}


def split_text(text, *, max_tokens=None, overlap_tokens=None):
    max_tokens = max_tokens or settings.RAG_CHUNK_TOKENS
    overlap_tokens = settings.RAG_CHUNK_OVERLAP_TOKENS if overlap_tokens is None else overlap_tokens
    if max_tokens < 20 or overlap_tokens < 0 or overlap_tokens >= max_tokens:
        raise ValueError("Chunk size and overlap are invalid.")
    cleaned = re.sub(r"[ \t]+", " ", text or "").strip()
    if not cleaned:
        return []
    token_matches = list(re.finditer(r"\S+", cleaned))
    chunks = []
    start_token = 0
    while start_token < len(token_matches):
        end_token = min(start_token + max_tokens, len(token_matches))
        start_character = token_matches[start_token].start()
        end_character = token_matches[end_token - 1].end()
        chunks.append(cleaned[start_character:end_character].strip())
        if end_token >= len(token_matches):
            break
        start_token = end_token - overlap_tokens
    return chunks


def selected_link_page_numbers(link, *, include_all=False):
    if link.page_from is None:
        return []
    page_to = link.page_to or link.page_from
    all_pages = list(range(link.page_from, page_to + 1))
    if include_all or len(all_pages) <= 8:
        return all_pages
    return sorted({*all_pages[:5], *all_pages[-3:]})


def extract_project_linked_pages(project, *, force=False, include_all=False):
    grouped_pages = defaultdict(set)
    grouped_sections = defaultdict(dict)
    links = ProjectDocumentLink.objects.filter(project=project).select_related("document")
    for link in links:
        for page_number in selected_link_page_numbers(link, include_all=include_all):
            grouped_pages[link.document_id].add(page_number)
            if link.section:
                grouped_sections[link.document_id][page_number] = link.section

    extracted = []
    for document_id, page_numbers in grouped_pages.items():
        extracted.extend(
            extract_document_pages(
                document_id,
                page_numbers,
                force=force,
                sections=grouped_sections[document_id],
            )
        )
    return extracted


def materialize_reviewed_page_chunks(project):
    created_or_updated = []
    links = ProjectDocumentLink.objects.filter(project=project).select_related("document")
    for link in links:
        if link.page_from is None:
            continue
        page_to = link.page_to or link.page_from
        rejected_or_unreviewed_pages = link.document.pages.filter(
            page_number__gte=link.page_from,
            page_number__lte=page_to,
        ).exclude(review_status__in=ACCEPTED_REVIEW_STATUSES)
        DocumentChunk.objects.filter(page__in=rejected_or_unreviewed_pages).delete()
        pages = link.document.pages.filter(
            page_number__gte=link.page_from,
            page_number__lte=page_to,
            review_status__in=ACCEPTED_REVIEW_STATUSES,
        )
        for page in pages:
            page_chunks = split_text(page.extracted_text)
            for index, text in enumerate(page_chunks):
                chunk, _ = DocumentChunk.objects.update_or_create(
                    page=page,
                    chunk_index=index,
                    defaults={
                        "text": text,
                        "section": page.section or link.section,
                        "token_count": len(re.findall(r"\S+", text)),
                        "metadata": {
                            "project_id": str(project.id),
                            "relationship": link.relationship,
                            "review_status": page.review_status,
                        },
                    },
                )
                created_or_updated.append(chunk)
            page.chunks.filter(chunk_index__gte=len(page_chunks)).delete()
    return created_or_updated


def project_evidence_payloads(project):
    payloads = []
    links = ProjectDocumentLink.objects.filter(project=project).select_related(
        "document",
        "document__local_government",
        "document__fiscal_year",
    )
    for link in links:
        metadata = {
            "project_id": str(project.id),
            "project_code": project.code,
            "link_id": link.id,
            "source_kind": "curated_project_evidence",
            "document_id": str(link.document_id),
            "document_title": link.document.title_en,
            "document_type": link.document.document_type,
            "relationship": link.relationship,
            "page": link.page_from,
            "page_to": link.page_to,
            "section": link.section,
            "source_url": link.document.source_url,
            "local_government": link.document.local_government.code,
            "fiscal_year": link.document.fiscal_year.code,
            "language": link.document.language,
            "data_classification": link.document.data_classification,
        }
        text = "\n".join(
            item
            for item in [
                link.document.title_en,
                link.document.title_np,
                link.section,
                link.evidence_note_en,
                link.evidence_note_np,
            ]
            if item
        )
        payloads.append(
            DocumentChunkPayload(id=f"project-link-{link.id}", text=text, metadata=metadata)
        )

        if link.page_from is None:
            continue
        page_to = link.page_to or link.page_from
        chunks = DocumentChunk.objects.filter(
            page__document=link.document,
            page__page_number__gte=link.page_from,
            page__page_number__lte=page_to,
            page__review_status__in=ACCEPTED_REVIEW_STATUSES,
        ).select_related("page")
        for chunk in chunks:
            chunk_metadata = {
                **metadata,
                "source_kind": "reviewed_document_page",
                "page": chunk.page.page_number,
                "section": chunk.section or chunk.page.section or link.section,
                "review_status": chunk.page.review_status,
                "chunk_index": chunk.chunk_index,
            }
            embedding_text = "\n".join(
                item
                for item in [
                    project.title_en,
                    project.title_np,
                    link.document.title_en,
                    link.document.title_np,
                    chunk_metadata["section"],
                    chunk.text,
                ]
                if item
            )
            payloads.append(
                DocumentChunkPayload(
                    id=f"document-chunk-{chunk.id}",
                    text=chunk.text,
                    metadata=chunk_metadata,
                    embedding_text=embedding_text,
                )
            )
    return payloads
