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


def _evidence_event(facts, event_type):
    return next(
        (
            event
            for event in facts.get("evidence_events", [])
            if event.get("event_type") == event_type
        ),
        None,
    )


def _event_date(facts, event_type):
    event = _evidence_event(facts, event_type)
    return event.get("date_bs") if event else None


def _source_reference(citations, language):
    if not citations:
        return ""
    citation = citations[0]
    page = citation.get("page")
    title = (
        citation.get("document_title_np")
        if language == QuestionLanguage.NEPALI and citation.get("document_title_np")
        else citation.get("document_title")
    )
    if language == QuestionLanguage.NEPALI:
        return f" स्रोत: {title}, पृष्ठ {page}।" if page else f" स्रोत: {title}।"
    if language == QuestionLanguage.ROMANIZED_NEPALI:
        return f" Source: {title}, page {page}." if page else f" Source: {title}."
    return f" Source: {title}, page {page}." if page else f" Source: {title}."


def _question_focus(question):
    text = question.casefold()
    if any(term in text for term in ("paid", "payment", "spent", "भुक्तानी", "खर्च", "bhuktani")):
        return "payment"
    if any(term in text for term in ("contract", "award", "ठेक्का", "thekka")):
        return "contract"
    if any(term in text for term in ("agreement", "सम्झौता", "samjhauta")):
        return "agreement"
    if any(term in text for term in ("monitoring", "अनुगमन", "anugaman")):
        return "monitoring"
    if any(term in text for term in ("progress", "completion", "प्रगति", "सम्पन्न")):
        return "progress"
    return "allocation"


def _english_database_answer(question, facts):
    focus = _question_focus(question)
    if focus == "payment":
        if facts["payments"]["reported_total"] is None:
            payment_date = _event_date(facts, "payment_date_recorded")
            if payment_date:
                return (
                    f"The official source records {payment_date} BS as the payment date, "
                    "but it does not publish the paid amount. The amount remains unknown, "
                    "not zero."
                )
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
    if focus == "agreement":
        agreement_date = _event_date(facts, "agreement_recorded")
        return (
            f"The official source records the agreement date as {agreement_date} BS."
            if agreement_date
            else "No verified agreement date is available."
        )
    if focus == "monitoring":
        monitoring_date = _event_date(facts, "monitoring_recorded")
        return (
            f"The official source records the monitoring date as {monitoring_date} BS."
            if monitoring_date
            else "No verified monitoring date is available."
        )
    if focus == "progress":
        progress = facts["progress"]["official_percent"]
        status = facts["progress"]["official_status"]
        return (
            f"The official project status is {status.replace('_', ' ')}, but no numeric "
            "completion percentage is published."
            if progress is None and status != "unknown"
            else "No verified official progress percentage is available."
            if progress is None
            else f"The reported official progress is {progress}%."
        )
    amount = facts["budget"]["allocated_amount"]
    return (
        f"The database records an allocation of {_money(amount)}. It is classified as "
        f"{facts['budget']['classification'].replace('_', ' ')}, not as a payment."
        if amount is not None
        else "No verified allocation amount is available."
    )


def _nepali_database_answer(question, facts):
    focus = _question_focus(question)
    if focus == "payment":
        payment_date = _event_date(facts, "payment_date_recorded")
        return (
            f"आधिकारिक स्रोतमा {payment_date} वि.सं. भुक्तानी मिति उल्लेख छ तर भुक्तानी "
            "रकम प्रकाशित छैन। रकम अज्ञात हो, शून्य होइन।"
            if facts["payments"]["reported_total"] is None and payment_date
            else (
                "उपलब्ध डाटामा प्रमाणित भुक्तानी अभिलेख छैन। यसको अर्थ रकम शून्य होइन; अवस्था अज्ञात छ।"
                if facts["payments"]["reported_total"] is None
                else f"डाटाबेसमा जम्मा भुक्तानी {_money(facts['payments']['reported_total'])} उल्लेख छ।"
            )
        )
    if focus == "contract":
        return (
            "प्रमाणित ठेक्का प्रदान, विजेता ठेकेदार वा सम्झौता रकम उपलब्ध छैन। "
            "बोलपत्र अनुमानलाई ठेक्का रकम मान्न मिल्दैन।"
            if facts["contract"]["amount"] is None
            else f"प्रमाणित सम्झौता रकम {_money(facts['contract']['amount'])} हो।"
        )
    if focus == "agreement":
        agreement_date = _event_date(facts, "agreement_recorded")
        return (
            f"आधिकारिक स्रोतमा सम्झौता मिति {agreement_date} वि.सं. उल्लेख छ।"
            if agreement_date
            else "प्रमाणित सम्झौता मिति उपलब्ध छैन।"
        )
    if focus == "monitoring":
        monitoring_date = _event_date(facts, "monitoring_recorded")
        return (
            f"आधिकारिक स्रोतमा अनुगमन मिति {monitoring_date} वि.सं. उल्लेख छ।"
            if monitoring_date
            else "प्रमाणित अनुगमन मिति उपलब्ध छैन।"
        )
    if focus == "progress":
        progress = facts["progress"]["official_percent"]
        status = facts["progress"]["official_status"]
        return (
            f"आधिकारिक आयोजना स्थिति {status} छ तर सम्पन्नताको सङ्ख्यात्मक प्रतिशत प्रकाशित छैन।"
            if progress is None and status != "unknown"
            else (
                "प्रमाणित आधिकारिक प्रगति प्रतिशत उपलब्ध छैन।"
                if progress is None
                else f"अभिलेखमा आधिकारिक प्रगति {progress}% छ।"
            )
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
        payment_date = _event_date(facts, "payment_date_recorded")
        return (
            f"Official source ma payment date {payment_date} BS record cha, tara paid "
            "amount publish bhayeko chaina. Amount unknown ho, zero hoina."
            if facts["payments"]["reported_total"] is None and payment_date
            else (
                "Upalabdha data ma verified payment record chaina. Yo zero kharcha hoina; "
                "awastha ajhai unknown cha."
                if facts["payments"]["reported_total"] is None
                else (
                    "Database ma total payment "
                    f"{_money(facts['payments']['reported_total'])} report bhayeko cha."
                )
            )
        )
    if focus == "contract":
        return (
            "Verified contract award, winning contractor, ra contract amount upalabdha "
            "chaina. Tender estimate lai award manna mildaina."
            if facts["contract"]["amount"] is None
            else f"Verified contract amount {_money(facts['contract']['amount'])} ho."
        )
    if focus == "agreement":
        agreement_date = _event_date(facts, "agreement_recorded")
        return (
            f"Official source ma agreement date {agreement_date} BS record cha."
            if agreement_date
            else "Verified agreement date upalabdha chaina."
        )
    if focus == "monitoring":
        monitoring_date = _event_date(facts, "monitoring_recorded")
        return (
            f"Official source ma monitoring date {monitoring_date} BS record cha."
            if monitoring_date
            else "Verified monitoring date upalabdha chaina."
        )
    if focus == "progress":
        progress = facts["progress"]["official_percent"]
        status = facts["progress"]["official_status"]
        if progress is not None:
            return f"Official progress {progress}% report bhayeko cha."
        if status != "unknown":
            return (
                f"Official project status {status.replace('_', ' ')} cha, tara numeric "
                "completion percentage publish bhayeko chaina."
            )
        return "Verified official progress percentage upalabdha chaina."
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


def _complete_project_answer(facts, citations, language):
    allocation = _money(facts["budget"]["allocated_amount"])
    contract = _money(facts["contract"]["amount"])
    paid = _money(facts["payments"]["reported_total"])
    progress = facts["progress"]["official_percent"]
    payment_count = len(facts["payments"]["records"])
    contractor = next(
        (item["award"]["contractor"]["name"] for item in facts["procurement"] if item["award"]),
        "unknown",
    )
    if language == QuestionLanguage.NEPALI:
        answer = (
            f"यस पूर्ण प्रदर्शन विवरणमा विनियोजन {allocation}, ठेक्का रकम {contract}, र "
            f"{payment_count} वटा भुक्तानीको जम्मा {paid} छ। ठेकेदार {contractor} र प्रतिवेदित "
            f"भौतिक प्रगति {progress}% छ। उपलब्ध संरचित विवरणले विनियोजनदेखि ठेक्का, भुक्तानी, "
            "उपलब्धि र स्थानसम्मको रकम यात्रा देखाउँछ।"
        )
    elif language == QuestionLanguage.ROMANIZED_NEPALI:
        answer = (
            f"Yo complete showcase trail ma allocation {allocation}, contract {contract}, ra "
            f"{payment_count} payment ko total {paid} cha. Contractor {contractor} ho ra "
            f"reported physical progress {progress}% cha. Structured data le allocation dekhi "
            "contract, payment, milestone, ra location samma ko money trail dekhauncha."
        )
    else:
        answer = (
            f"This complete showcase trail records an allocation of {allocation}, a contract of "
            f"{contract}, and {payment_count} payments totalling {paid}. The contractor is "
            f"{contractor}, and reported physical progress is {progress}%. The structured trail "
            "connects allocation, procurement, award, payments, milestones, and location."
        )
    return answer + _source_reference(citations, language)


def _project_answer(facts, citations, language):
    if not facts["unknown_fields"]:
        return _complete_project_answer(facts, citations, language)
    allocation = _money(facts["budget"]["allocated_amount"])
    estimates = [
        _money(item["estimated_amount"])
        for item in facts["procurement"]
        if item["estimated_amount"] is not None
    ]
    estimate = estimates[0] if estimates else None
    audit_notes = [item["evidence_note"] for item in citations if item["relationship"] == "audit"]
    agreement_date = _event_date(facts, "agreement_recorded")
    monitoring_date = _event_date(facts, "monitoring_recorded")
    payment_date = _event_date(facts, "payment_date_recorded")
    progress = facts["progress"]["official_percent"]
    project_status = facts["progress"]["official_status"]
    contract_unknown = facts["contract"]["amount"] is None
    payment_unknown = facts["payments"]["reported_total"] is None

    if language == QuestionLanguage.NEPALI:
        parts = [
            f"उपलब्ध प्रमाणअनुसार यस आयोजनामा {allocation} विनियोजन देखिन्छ।"
            if allocation
            else "प्रमाणित विनियोजन रकम उपलब्ध छैन।"
        ]
        if estimate:
            parts.append(f"जोडिएको बोलपत्रमा {estimate} अनुमान छ; यो ठेक्का प्रदान वा भुक्तानी रकम होइन।")
        dated_events = []
        if agreement_date:
            dated_events.append(f"सम्झौता {agreement_date}")
        if monitoring_date:
            dated_events.append(f"अनुगमन {monitoring_date}")
        if payment_date:
            dated_events.append(f"भुक्तानी मिति {payment_date}")
        if dated_events:
            parts.append("आधिकारिक प्रतिवेदनमा " + ", ".join(dated_events) + " वि.सं. उल्लेख छन्।")
        if payment_date and payment_unknown:
            parts.append(
                "भुक्तानी मिति अभिलेख छ तर वास्तविक भुक्तानी रकम प्रकाशित छैन; रकम शून्य मानिएको छैन।"
            )
        elif payment_unknown:
            parts.append("प्रमाणित भुक्तानी रकम उपलब्ध छैन; यसको अर्थ शून्य खर्च होइन।")
        if contract_unknown:
            parts.append("प्रमाणित ठेक्का रकम र जिम्मेवार पक्षको पूर्ण अभिलेख उपलब्ध छैन।")
        if progress is None and project_status != "unknown":
            parts.append(
                f"आयोजनाको आधिकारिक स्थिति {project_status} छ तर सम्पन्नताको "
                "सङ्ख्यात्मक प्रतिशत प्रकाशित छैन।"
            )
        if audit_notes:
            parts.append(audit_notes[0])
        parts.append("त्यसैले उपलब्ध प्रमाणले सबै पैसा कहाँ गयो भन्ने पूर्ण निष्कर्ष अझै दिँदैन।")
        return " ".join(parts) + _source_reference(citations, language)

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
        dated_events = []
        if agreement_date:
            dated_events.append(f"agreement {agreement_date}")
        if monitoring_date:
            dated_events.append(f"monitoring {monitoring_date}")
        if payment_date:
            dated_events.append(f"payment date {payment_date}")
        if dated_events:
            parts.append("Official report ma " + ", ".join(dated_events) + " BS record cha.")
        if payment_date and payment_unknown:
            parts.append(
                "Payment date record cha tara actual paid amount publish bhayeko chaina; "
                "amount lai zero maniyeko chaina."
            )
        elif payment_unknown:
            parts.append("Verified payment amount chaina; yo zero spending bhanne hoina.")
        if contract_unknown:
            parts.append("Verified contract amount ra responsible party ko complete record chaina.")
        if progress is None and project_status != "unknown":
            parts.append(
                f"Official status {project_status.replace('_', ' ')} cha tara numeric "
                "completion percentage publish bhayeko chaina."
            )
        if audit_notes:
            parts.append(
                "Audit citation ma related record cha, tara ledger rows human review bina "
                "jodna mildaina."
            )
        parts.append(
            "Tyasaile sabai paisa kaha gayo bhanera ahile complete conclusion dina mildaina."
        )
        return " ".join(parts) + _source_reference(citations, language)

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
    dated_events = []
    if agreement_date:
        dated_events.append(f"agreement {agreement_date}")
    if monitoring_date:
        dated_events.append(f"monitoring {monitoring_date}")
    if payment_date:
        dated_events.append(f"payment date {payment_date}")
    if dated_events:
        parts.append("The official report records " + ", ".join(dated_events) + " BS.")
    if payment_date and payment_unknown:
        parts.append(
            "A payment date is recorded, but the actual paid amount is not published; "
            "the missing amount is not treated as zero."
        )
    elif payment_unknown:
        parts.append("No verified payment amount is available; this does not mean zero spending.")
    if contract_unknown:
        parts.append(
            "No verified contract amount or complete responsible-party record is available."
        )
    if progress is None and project_status != "unknown":
        parts.append(
            f"The official status is {project_status.replace('_', ' ')}, but no numeric "
            "completion percentage is published."
        )
    if audit_notes:
        parts.append(audit_notes[0])
    parts.append("The available evidence therefore cannot yet establish where all the money went.")
    return " ".join(parts) + _source_reference(citations, language)


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
