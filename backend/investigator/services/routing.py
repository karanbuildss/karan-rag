import re
from enum import StrEnum


class InvestigationRoute(StrEnum):
    DATABASE_QUERY = "DATABASE_QUERY"
    DOCUMENT_RAG = "DOCUMENT_RAG"
    ANOMALY_EXPLANATION = "ANOMALY_EXPLANATION"
    PROJECT_INVESTIGATION = "PROJECT_INVESTIGATION"
    GENERAL_HELP = "GENERAL_HELP"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class QuestionLanguage(StrEnum):
    ENGLISH = "en"
    NEPALI = "ne"
    ROMANIZED_NEPALI = "romanized_ne"


ROMANIZED_MARKERS = {
    "cha",
    "chha",
    "gayo",
    "kaha",
    "kati",
    "kina",
    "ko",
    "ma",
    "paisa",
    "yojana",
    "wada",
    "ward",
    "bhuktani",
    "thekka",
}


def detect_language(question):
    if re.search(r"[\u0900-\u097f]", question):
        return QuestionLanguage.NEPALI
    words = set(re.findall(r"[a-z]+", question.lower()))
    if len(words & ROMANIZED_MARKERS) >= 2:
        return QuestionLanguage.ROMANIZED_NEPALI
    return QuestionLanguage.ENGLISH


def _contains(text, phrases):
    return any(phrase in text for phrase in phrases)


def route_question(question, *, has_project):
    text = question.casefold()
    if not has_project:
        if _contains(text, ("help", "what can", "how to", "के गर्न", "मद्दत")):
            return InvestigationRoute.GENERAL_HELP
        return InvestigationRoute.INSUFFICIENT_EVIDENCE

    money_journey = (
        "where did",
        "where has",
        "money go",
        "paisa kaha",
        "paisa kata",
        "paisa kaha",
        "पैसा कहाँ",
        "पैसा कता",
        "रकम कहाँ",
        "money trail",
        "investigate",
        "जाँच",
    )
    if _contains(text, money_journey):
        return InvestigationRoute.PROJECT_INVESTIGATION

    anomaly_terms = (
        "why flagged",
        "why is this flagged",
        "anomaly",
        "unusual pattern",
        "review recommended",
        "flagged",
        "kina flag",
        "kina flagged",
        "सङ्गति",
        "असामान्य",
        "किन चिन्ह",
    )
    if _contains(text, anomaly_terms):
        return InvestigationRoute.ANOMALY_EXPLANATION

    document_terms = (
        "audit",
        "document",
        "report say",
        "tender say",
        "budget book say",
        "source say",
        "evidence",
        "लेखापरीक्षण",
        "कागजात",
        "प्रतिवेदन",
        "प्रमाण",
        "bolpatra",
    )
    if _contains(text, document_terms):
        return InvestigationRoute.DOCUMENT_RAG

    database_terms = (
        "how much",
        "allocated",
        "allocation",
        "budget",
        "spent",
        "paid",
        "payment",
        "contract amount",
        "progress",
        "कति",
        "विनियोजन",
        "बजेट",
        "खर्च",
        "भुक्तानी",
        "प्रगति",
        "kati",
        "budget",
        "bhuktani",
    )
    if _contains(text, database_terms):
        return InvestigationRoute.DATABASE_QUERY

    return InvestigationRoute.PROJECT_INVESTIGATION
