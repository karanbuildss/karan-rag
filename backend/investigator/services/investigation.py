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


def _visualizations(facts):
    if not facts:
        return []
    financial_rows = [
        {
            "key": "allocated",
            "label_en": "Allocated",
            "label_np": "विनियोजित",
            "value": facts["budget"]["allocated_amount"],
        },
        {
            "key": "contracted",
            "label_en": "Contracted",
            "label_np": "ठेक्का रकम",
            "value": facts["contract"]["amount"],
        },
        {
            "key": "paid",
            "label_en": "Reported paid",
            "label_np": "प्रतिवेदित भुक्तानी",
            "value": facts["payments"]["reported_total"],
        },
    ]
    visualizations = []
    if any(row["value"] is not None for row in financial_rows):
        visualizations.append(
            {
                "id": "financial_flow",
                "type": "bar",
                "title_en": "Allocation, contract, and reported payments",
                "title_np": "विनियोजन, ठेक्का र प्रतिवेदित भुक्तानी",
                "unit": "NPR",
                "data": financial_rows,
                "boundary_en": "Unknown values are omitted, never converted to zero.",
                "boundary_np": "अज्ञात मानलाई शून्यमा परिवर्तन नगरी छोडिएको छ।",
            }
        )

    contract_amount = facts["contract"]["amount"]
    paid_amount = facts["payments"]["reported_total"]
    progress = facts["progress"]["official_percent"]
    if contract_amount is not None and paid_amount is not None and progress is not None:
        payment_percent = round(float(paid_amount) / float(contract_amount) * 100, 2)
        visualizations.append(
            {
                "id": "payment_progress",
                "type": "bar",
                "title_en": "Payment versus physical progress",
                "title_np": "भुक्तानी र भौतिक प्रगति तुलना",
                "unit": "percent",
                "data": [
                    {
                        "key": "payment_percent",
                        "label_en": "Contract paid",
                        "label_np": "ठेक्का भुक्तानी",
                        "value": payment_percent,
                    },
                    {
                        "key": "physical_progress",
                        "label_en": "Physical progress",
                        "label_np": "भौतिक प्रगति",
                        "value": float(progress),
                    },
                ],
                "boundary_en": (
                    "A difference is a review signal and may have legitimate timing or "
                    "mobilization explanations."
                ),
                "boundary_np": ("अन्तर समीक्षा सङ्केत हो; समय वा परिचालन पेश्कीजस्ता वैध कारण हुन सक्छन्।"),
            }
        )
    return visualizations


def _ensure_classification_boundary(answer, language, facts):
    if not facts or facts["project"]["data_classification"] != "synthetic_demo":
        return answer
    notices = {
        QuestionLanguage.ENGLISH: (
            " This is explicitly labelled synthetic demonstration data, not an official "
            "government record."
        ),
        QuestionLanguage.NEPALI: (
            " यो स्पष्ट रूपमा कृत्रिम प्रदर्शन तथ्याङ्क हो, आधिकारिक सरकारी अभिलेख होइन।"
        ),
        QuestionLanguage.ROMANIZED_NEPALI: (
            " Yo explicitly synthetic demo data ho, official government record hoina."
        ),
    }
    notice = notices.get(language, notices[QuestionLanguage.ENGLISH])
    markers = ("synthetic", "कृत्रिम")
    return answer if any(marker in answer.casefold() for marker in markers) else answer + notice


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
        if facts["payments"]["status"] == "date_reported_amount_missing":
            messages.append(
                {
                    "code": "payment_amount_unpublished",
                    "message": (
                        "An official payment date is recorded, but no verified paid amount "
                        "is available; the amount remains unknown, not zero."
                    ),
                }
            )
        else:
            messages.append(
                {
                    "code": "payments_not_reported",
                    "message": (
                        "No verified payment records are available; this does not mean "
                        "zero spending."
                    ),
                }
            )
    if "official_progress" in unknown:
        if facts["progress"]["official_status"] != "unknown":
            messages.append(
                {
                    "code": "progress_percentage_unpublished",
                    "message": (
                        "An official implementation status is available, but no numeric "
                        "completion percentage is published."
                    ),
                }
            )
        else:
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

    answer = _ensure_classification_boundary(answer, language, facts)

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
        "visualizations": _visualizations(facts),
        "limitations": _limitations(facts),
        "provenance": {
            "structured_values": "relational_database",
            "document_retrieval": retrieval_provider,
            "answer_generation": generation_provider,
            "anomaly_analysis": "deterministic_rules",
        },
    }
