from decimal import Decimal, InvalidOperation

from investigator.services.routing import InvestigationRoute, QuestionLanguage


def _money(value):
    if value is None:
        return None
    try:
        amount = Decimal(str(value))
    except InvalidOperation:
        return str(value)
    return f"NPR {amount:,.2f}"


def _question_focus(question):
    text = question.casefold()
    if any(term in text for term in ("paid", "payment", "spent", "भुक्तानी", "खर्च", "bhuktani")):
        return "payment"
    if any(term in text for term in ("contract", "award", "ठेक्का", "thekka")):
        return "contract"
    if any(term in text for term in ("progress", "completion", "प्रगति", "सम्पन्न")):
        return "progress"
    return "allocation"


def _english_database_answer(question, facts):
    focus = _question_focus(question)
    if focus == "payment":
        if facts["payments"]["reported_total"] is None:
            return (
                "No verified payment records have been reported in the available data. "
                "This is unknown, not zero spending."
            )
        return (
            f"The database reports total payments of {_money(facts['payments']['reported_total'])}."
        )
    if focus == "contract":
        if facts["contract"]["amount"] is None:
            return (
                "No verified contract award, winning contractor, or contract amount is "
                "available. A tender estimate must not be treated as an award."
            )
        return f"The verified contract amount is {_money(facts['contract']['amount'])}."
    if focus == "progress":
        progress = facts["progress"]["official_percent"]
        return (
            "No verified official progress percentage is available."
            if progress is None
            else f"The reported official progress is {progress}%."
        )
    amount = facts["budget"]["allocated_amount"]
    return (
        f"The database records an allocation of {_money(amount)}. It is classified as "
        "reconstructed from official sources, not as a payment."
        if amount is not None
        else "No verified allocation amount is available."
    )


def _nepali_database_answer(question, facts):
    focus = _question_focus(question)
    if focus == "payment":
        return (
            "उपलब्ध डाटामा प्रमाणित भुक्तानी अभिलेख छैन। यसको अर्थ रकम शून्य होइन; अवस्था अज्ञात छ।"
            if facts["payments"]["reported_total"] is None
            else f"डाटाबेसमा जम्मा भुक्तानी {_money(facts['payments']['reported_total'])} उल्लेख छ।"
        )
    if focus == "contract":
        return (
            "प्रमाणित ठेक्का प्रदान, विजेता ठेकेदार वा सम्झौता रकम उपलब्ध छैन। "
            "बोलपत्र अनुमानलाई ठेक्का रकम मान्न मिल्दैन।"
            if facts["contract"]["amount"] is None
            else f"प्रमाणित सम्झौता रकम {_money(facts['contract']['amount'])} हो।"
        )
    if focus == "progress":
        progress = facts["progress"]["official_percent"]
        return (
            "प्रमाणित आधिकारिक प्रगति प्रतिशत उपलब्ध छैन।"
            if progress is None
            else f"अभिलेखमा आधिकारिक प्रगति {progress}% छ।"
        )
    amount = facts["budget"]["allocated_amount"]
    return (
        f"डाटाबेसमा {_money(amount)} विनियोजन देखिन्छ। यो आधिकारिक स्रोतबाट "
        "पुनर्निर्मित रकम हो, भुक्तानी होइन।"
        if amount is not None
        else "प्रमाणित विनियोजन रकम उपलब्ध छैन।"
    )


def _romanized_database_answer(question, facts):
    focus = _question_focus(question)
    if focus == "payment":
        return (
            "Upalabdha data ma verified payment record chaina. Yo zero kharcha hoina; "
            "awastha ajhai unknown cha."
            if facts["payments"]["reported_total"] is None
            else (
                "Database ma total payment "
                f"{_money(facts['payments']['reported_total'])} report bhayeko cha."
            )
        )
    if focus == "contract":
        return (
            "Verified contract award, winning contractor, ra contract amount upalabdha "
            "chaina. Tender estimate lai award manna mildaina."
            if facts["contract"]["amount"] is None
            else f"Verified contract amount {_money(facts['contract']['amount'])} ho."
        )
    amount = facts["budget"]["allocated_amount"]
    return (
        f"Database ma {_money(amount)} allocation dekhincha. Yo official source bata "
        "reconstructed ho, payment hoina."
        if amount is not None
        else "Verified allocation amount upalabdha chaina."
    )


def _document_answer(citations, language):
    if not citations:
        return insufficient_answer(language)
    notes = [citation["evidence_note"] for citation in citations if citation["evidence_note"]]
    if language == QuestionLanguage.NEPALI:
        return "उपलब्ध स्रोत कागजातले यस्तो देखाउँछन्: " + " ".join(notes)
    if language == QuestionLanguage.ROMANIZED_NEPALI:
        return (
            "Available source evidence ko summary: "
            + " ".join(notes)
            + " Exact claim ko lagi tala ko cited page hernuhos."
        )
    return "The available source documents show: " + " ".join(notes)


def _project_answer(facts, citations, language):
    allocation = _money(facts["budget"]["allocated_amount"])
    estimates = [
        _money(item["estimated_amount"])
        for item in facts["procurement"]
        if item["estimated_amount"] is not None
    ]
    estimate = estimates[0] if estimates else None
    audit_notes = [item["evidence_note"] for item in citations if item["relationship"] == "audit"]

    if language == QuestionLanguage.NEPALI:
        parts = [
            f"उपलब्ध प्रमाणअनुसार यस आयोजनामा {allocation} विनियोजन देखिन्छ।"
            if allocation
            else "प्रमाणित विनियोजन रकम उपलब्ध छैन।"
        ]
        if estimate:
            parts.append(f"जोडिएको बोलपत्रमा {estimate} अनुमान छ; यो ठेक्का प्रदान वा भुक्तानी रकम होइन।")
        parts.append(
            "प्रमाणित ठेक्का प्रदान, विजेता ठेकेदार र भुक्तानी अभिलेख उपलब्ध छैनन्, "
            "त्यसैले सबै पैसा कहाँ गयो भनेर अहिले निष्कर्ष निकाल्न मिल्दैन।"
        )
        if audit_notes:
            parts.append(audit_notes[0])
        return " ".join(parts)

    if language == QuestionLanguage.ROMANIZED_NEPALI:
        parts = [
            f"Upalabdha praman anusar yo project ko allocation {allocation} cha."
            if allocation
            else "Verified allocation amount upalabdha chaina."
        ]
        if estimate:
            parts.append(
                f"Linked tender ma {estimate} estimate cha; yo contract award wa payment "
                "amount hoina."
            )
        parts.append(
            "Verified award, winning contractor, ra payment record chaina, tyasaile sabai "
            "paisa kaha gayo bhanera ahile nischit bhanna mildaina."
        )
        if audit_notes:
            parts.append(
                "Audit citation ma related record cha, tara ledger rows human review bina "
                "jodna mildaina."
            )
        return " ".join(parts)

    parts = [
        f"Available evidence shows an allocation of {allocation} for this project."
        if allocation
        else "No verified allocation amount is available."
    ]
    if estimate:
        parts.append(
            f"The linked tender lists an estimate of {estimate}; this is not a contract "
            "award or payment amount."
        )
    parts.append(
        "No verified contract award, winning contractor, or payment record is available, "
        "so the evidence cannot yet establish where all the money went."
    )
    if audit_notes:
        parts.append(audit_notes[0])
    return " ".join(parts)


def insufficient_answer(language):
    if language == QuestionLanguage.NEPALI:
        return "उपलब्ध कागजात र संरचित डाटामा पर्याप्त प्रमाण छैन।"
    if language == QuestionLanguage.ROMANIZED_NEPALI:
        return "Upalabdha document ra structured data ma pugdo praman chaina."
    return "I do not have enough evidence in the available documents and structured data."


def _anomaly_answer(anomalies, language):
    if not anomalies:
        if language == QuestionLanguage.NEPALI:
            return "यस आयोजनामा हाल कुनै सक्रिय विसङ्गति सूचक छैन। यसको अर्थ सबै प्रमाण पूर्ण छन् भन्ने होइन।"
        if language == QuestionLanguage.ROMANIZED_NEPALI:
            return (
                "Yo project ma ahile active anomaly indicator chaina. Yasle sabai "
                "evidence complete cha bhanne hoina."
            )
        return (
            "This project currently has no active anomaly indicators. This does not mean "
            "that every supporting record is complete."
        )

    selected = anomalies[:3]
    if language == QuestionLanguage.NEPALI:
        details = " ".join(
            f"{item['title_np']}: {item['reason_np']} सिफारिस: {item['recommendation_np']}"
            for item in selected
        )
        return (
            f"यस आयोजनामा {len(anomalies)} सक्रिय समीक्षा सूचक छन्। {details} "
            "यी सूचक समीक्षा गर्नुपर्ने ढाँचा हुन्, गलत कामको प्रमाण होइनन्।"
        )
    if language == QuestionLanguage.ROMANIZED_NEPALI:
        details = " ".join(
            f"{item['title_en']}: {item['reason_en']} Recommendation: {item['recommendation_en']}"
            for item in selected
        )
        return (
            f"Yo project ma {len(anomalies)} active review indicator chan. {details} "
            "Yi indicator review signal hun, wrongdoing ko proof hoina."
        )
    details = " ".join(
        f"{item['title_en']}: {item['reason_en']} Recommendation: {item['recommendation_en']}"
        for item in selected
    )
    return (
        f"This project has {len(anomalies)} active review indicators. {details} "
        "These indicators are review signals, not proof of wrongdoing."
    )


def compose_answer(question, route, language, facts, citations, anomalies=None):
    if route == InvestigationRoute.GENERAL_HELP:
        if language == QuestionLanguage.NEPALI:
            return "आयोजना छानेर विनियोजन, बोलपत्र, भुक्तानी, प्रगति वा स्रोत कागजातबारे प्रश्न सोध्नुहोस्।"
        if language == QuestionLanguage.ROMANIZED_NEPALI:
            return (
                "Project chhanera allocation, tender, payment, progress, wa source document "
                "bare sodhnuhos."
            )
        return (
            "Select a project, then ask about its allocation, tender, payments, progress, "
            "or source documents."
        )
    if route == InvestigationRoute.INSUFFICIENT_EVIDENCE or facts is None:
        return insufficient_answer(language)
    if route == InvestigationRoute.DATABASE_QUERY:
        if language == QuestionLanguage.NEPALI:
            return _nepali_database_answer(question, facts)
        if language == QuestionLanguage.ROMANIZED_NEPALI:
            return _romanized_database_answer(question, facts)
        return _english_database_answer(question, facts)
    if route == InvestigationRoute.DOCUMENT_RAG:
        return _document_answer(citations, language)
    if route == InvestigationRoute.ANOMALY_EXPLANATION:
        return _anomaly_answer(anomalies or [], language)
    return _project_answer(facts, citations, language)
