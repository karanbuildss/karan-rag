from anomalies.models import AnomalyFlag
from django.conf import settings

from investigator.services.composer import compose_answer
from investigator.services.facts import build_structured_facts
from investigator.services.generation import GenerationUnavailable, refine_with_ollama
from investigator.services.retrieval import retrieve_project_evidence
from investigator.services.routing import (
    InvestigationRoute,
    QuestionLanguage,
    detect_language,
    route_question,
)


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


def _active_anomalies(project):
    severity_order = {"high": 0, "medium": 1, "low": 2, "info": 3}
    flags = AnomalyFlag.objects.filter(
        project=project,
        status=AnomalyFlag.Status.ACTIVE,
    )
    rows = [
        {
            "id": str(flag.id),
            "rule_id": flag.rule_id,
            "rule_version": flag.rule_version,
            "severity": flag.severity,
            "reliability": flag.reliability,
            "title_en": flag.title_en,
            "title_np": flag.title_np,
            "reason_en": flag.reason_en,
            "reason_np": flag.reason_np,
            "data_used": flag.data_used,
            "threshold": flag.threshold,
            "calculated_values": flag.calculated_values,
            "possible_explanations": flag.possible_explanations,
            "recommendation_en": flag.recommendation_en,
            "recommendation_np": flag.recommendation_np,
            "source_references": flag.source_references,
            "last_evaluated_at": flag.last_evaluated_at,
        }
        for flag in flags
    ]
    return sorted(rows, key=lambda row: (severity_order[row["severity"]], row["rule_id"]))


def _anomaly_citations(anomalies):
    citations = []
    seen = set()
    for anomaly in anomalies:
        for source in anomaly["source_references"]:
            key = (source.get("document_id"), source.get("page"), source.get("section"))
            if key in seen:
                continue
            seen.add(key)
            page = source.get("page")
            citations.append(
                {
                    **source,
                    "document_title_np": "",
                    "page_to": page,
                    "relationship": "anomaly_source",
                    "evidence_note": "Source used by the deterministic anomaly rule.",
                    "excerpt": "",
                    "source_kind": "deterministic_anomaly_rule",
                    "review_status": "curated",
                    "viewer_path": (f"/documents/{source['document_id']}?page={page or 1}"),
                }
            )
    return citations


def investigate(*, question, project=None, requested_language="auto"):
    language = (
        detect_language(question)
        if requested_language == "auto"
        else QuestionLanguage(requested_language)
    )
    route = route_question(question, has_project=project is not None)
    facts = build_structured_facts(project) if project is not None else None
    anomalies = _active_anomalies(project) if project is not None else []
    citations = []
    retrieval_provider = "none"
    if project is not None and route == InvestigationRoute.ANOMALY_EXPLANATION:
        citations = _anomaly_citations(anomalies)
        retrieval_provider = "deterministic_anomaly_sources"
    elif project is not None:
        citations, retrieval_provider = retrieve_project_evidence(
            project,
            question,
            route,
            language,
        )
    answer = compose_answer(question, route, language, facts, citations, anomalies)
    generation_provider = "deterministic"
    if (
        settings.INVESTIGATOR_ENABLE_GENERATION
        and project is not None
        and language != QuestionLanguage.ROMANIZED_NEPALI
        and route != InvestigationRoute.ANOMALY_EXPLANATION
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
        "anomalies": anomalies,
        "citations": citations,
        "limitations": _limitations(facts),
        "provenance": {
            "structured_values": "relational_database",
            "document_retrieval": retrieval_provider,
            "answer_generation": generation_provider,
            "anomaly_analysis": "deterministic_rules",
        },
    }
