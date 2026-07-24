from django.conf import settings

from investigator.services.composer import compose_answer
from investigator.services.facts import build_structured_facts
from investigator.services.generation import GenerationUnavailable, refine_with_ollama
from investigator.services.retrieval import retrieve_project_evidence
from investigator.services.routing import QuestionLanguage, detect_language, route_question


def _limitations(facts):
    if not facts:
        return [
            {
                "code": "project_context_required",
                "message": "Select a project to investigate its structured data and evidence.",
            }
        ]
    messages = []
    unknown = set(facts["unknown_fields"])
    if {"contract_award", "winning_contractor", "contract_amount"} & unknown:
        messages.append(
            {
                "code": "contract_award_unknown",
                "message": "No verified contract-award record is available.",
            }
        )
    if "payments" in unknown:
        messages.append(
            {
                "code": "payments_not_reported",
                "message": (
                    "No verified payment records are available; this does not mean zero spending."
                ),
            }
        )
    if "official_progress" in unknown:
        messages.append(
            {
                "code": "progress_unknown",
                "message": "No verified official progress percentage is available.",
            }
        )
    if "exact_location" in unknown:
        messages.append(
            {
                "code": "location_unknown",
                "message": "Exact project coordinates have not been verified.",
            }
        )
    return messages


def investigate(*, question, project=None, requested_language="auto"):
    language = (
        detect_language(question)
        if requested_language == "auto"
        else QuestionLanguage(requested_language)
    )
    route = route_question(question, has_project=project is not None)
    facts = build_structured_facts(project) if project is not None else None
    citations = []
    retrieval_provider = "none"
    if project is not None:
        citations, retrieval_provider = retrieve_project_evidence(
            project,
            question,
            route,
            language,
        )
    answer = compose_answer(question, route, language, facts, citations)
    generation_provider = "deterministic"
    if (
        settings.INVESTIGATOR_ENABLE_GENERATION
        and project is not None
        and language != QuestionLanguage.ROMANIZED_NEPALI
    ):
        try:
            answer = refine_with_ollama(question, language, route, facts, citations, answer)
            generation_provider = f"ollama:{settings.OLLAMA_CHAT_MODEL}"
        except GenerationUnavailable:
            generation_provider = "deterministic_fallback"
    elif language == QuestionLanguage.ROMANIZED_NEPALI:
        generation_provider = "deterministic_romanized"

    return {
        "question": question,
        "route": str(route),
        "language": str(language),
        "answer": answer,
        "project": (
            {
                "id": str(project.id),
                "code": project.code,
                "title_en": project.title_en,
                "title_np": project.title_np,
            }
            if project
            else None
        ),
        "structured_facts": facts,
        "citations": citations,
        "limitations": _limitations(facts),
        "provenance": {
            "structured_values": "relational_database",
            "document_retrieval": retrieval_provider,
            "answer_generation": generation_provider,
        },
    }
