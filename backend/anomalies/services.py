# ruff: noqa: E501

from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from documents.models import ProjectDocumentLink
from projects.models import Project, ProjectEvidenceEvent

from anomalies.models import AnomalyFlag


def _references(project, relationship):
    return [
        {
            "document_id": str(link.document_id),
            "document_title": link.document.title_en,
            "page": link.page_from,
            "section": link.section,
            "source_url": link.document.source_url,
        }
        for link in project.document_links.filter(relationship=relationship).select_related(
            "document"
        )
    ]


def _rule_payloads(project):
    tenders = list(project.tenders.select_related("award").all())
    awards = [getattr(tender, "award", None) for tender in tenders]
    awards = [award for award in awards if award]
    payments = [payment for award in awards for payment in award.payments.all()]
    procurement_sources = _references(project, ProjectDocumentLink.Relationship.PROCUREMENT)
    audit_sources = _references(project, ProjectDocumentLink.Relationship.AUDIT)
    progress_sources = _references(project, ProjectDocumentLink.Relationship.PROGRESS)
    evidence_events = list(project.evidence_events.all())
    events_by_type = {event.event_type: event for event in evidence_events}
    agreement_event = events_by_type.get(ProjectEvidenceEvent.EventType.AGREEMENT_RECORDED)
    monitoring_event = events_by_type.get(ProjectEvidenceEvent.EventType.MONITORING_RECORDED)
    payment_date_event = events_by_type.get(ProjectEvidenceEvent.EventType.PAYMENT_DATE_RECORDED)
    payloads = []

    if agreement_event and not awards:
        payloads.append(
            {
                "rule_id": "AGREEMENT_DATE_CONTRACT_DETAILS_MISSING",
                "severity": AnomalyFlag.Severity.LOW,
                "reliability": AnomalyFlag.Reliability.OFFICIAL_REFERENCE,
                "title_en": "Agreement date is recorded, but contract details are missing",
                "title_np": "सम्झौता मिति अभिलेख छ तर सम्झौता विवरण उपलब्ध छैन",
                "reason_en": f"The official progress source records an agreement date of {agreement_event.date_bs} BS, but no signed agreement, responsible-party record, or agreed amount is linked.",
                "reason_np": f"आधिकारिक प्रगति स्रोतमा {agreement_event.date_bs} वि.सं. सम्झौता मिति छ तर हस्ताक्षरित सम्झौता, जिम्मेवार पक्ष वा सम्झौता रकम जोडिएको छैन।",
                "data_used": {
                    "agreement_date_bs": agreement_event.date_bs,
                    "contract_award_count": len(awards),
                },
                "threshold": {
                    "agreement_date_recorded": True,
                    "contract_details_required": True,
                },
                "calculated_values": {},
                "possible_explanations": [
                    {
                        "en": "The work may have used a consumer committee or another non-tender implementation method.",
                        "np": "काम उपभोक्ता समिति वा अर्को गैर-बोलपत्र कार्यान्वयन विधिबाट भएको हुन सक्छ।",
                    },
                    {
                        "en": "The signed agreement may exist but has not been published or collected.",
                        "np": "हस्ताक्षरित सम्झौता हुन सक्छ तर प्रकाशित वा सङ्कलन गरिएको छैन।",
                    },
                ],
                "recommendation_en": "Collect the signed agreement or award record and verify the implementation method, responsible party, and agreed amount.",
                "recommendation_np": "हस्ताक्षरित सम्झौता वा ठेक्का प्रदान अभिलेख सङ्कलन गरी कार्यान्वयन विधि, जिम्मेवार पक्ष र सम्झौता रकम प्रमाणित गर्नुहोस्।",
                "source_references": progress_sources,
            }
        )

    if payment_date_event and not payments:
        payloads.append(
            {
                "rule_id": "PAYMENT_DATE_AMOUNT_MISSING",
                "severity": AnomalyFlag.Severity.LOW,
                "reliability": AnomalyFlag.Reliability.OFFICIAL_REFERENCE,
                "title_en": "Payment date is recorded, but the paid amount is missing",
                "title_np": "भुक्तानी मिति अभिलेख छ तर भुक्तानी रकम उपलब्ध छैन",
                "reason_en": f"The official progress source records {payment_date_event.date_bs} BS as the payment date, but no project-level payment amount or voucher is linked.",
                "reason_np": f"आधिकारिक प्रगति स्रोतमा {payment_date_event.date_bs} वि.सं. भुक्तानी मिति छ तर आयोजना-स्तरको भुक्तानी रकम वा भौचर जोडिएको छैन।",
                "data_used": {
                    "payment_date_bs": payment_date_event.date_bs,
                    "reported_payment_count": len(payments),
                },
                "threshold": {
                    "payment_date_recorded": True,
                    "payment_amount_required": True,
                },
                "calculated_values": {},
                "possible_explanations": [
                    {
                        "en": "The amount may be held in a voucher or project-level accounting transaction that is not publicly linked.",
                        "np": "रकम सार्वजनिक रूपमा नजोडिएको भौचर वा आयोजना-स्तरको लेखा कारोबारमा हुन सक्छ।",
                    }
                ],
                "recommendation_en": "Collect the final payment voucher or project-level SuTRA transaction before reporting a paid amount.",
                "recommendation_np": "भुक्तानी रकम रिपोर्ट गर्नुअघि अन्तिम भुक्तानी भौचर वा आयोजना-स्तरको SuTRA कारोबार सङ्कलन गर्नुहोस्।",
                "source_references": progress_sources,
            }
        )

    if tenders and not awards:
        payloads.append(
            {
                "rule_id": "EVIDENCE_AWARD_MISSING",
                "severity": AnomalyFlag.Severity.MEDIUM,
                "reliability": AnomalyFlag.Reliability.STRONG,
                "title_en": "Contract-award evidence is missing",
                "title_np": "ठेक्का प्रदान प्रमाण उपलब्ध छैन",
                "reason_en": "A procurement notice is linked, but the available dataset contains no contract-award record.",
                "reason_np": "खरिद सूचना जोडिएको छ तर उपलब्ध तथ्यमा ठेक्का प्रदान अभिलेख छैन।",
                "data_used": {"tender_count": len(tenders), "award_count": 0},
                "threshold": {"tender_count_min": 1, "award_count": 0},
                "calculated_values": {},
                "possible_explanations": [
                    {
                        "en": "The award may exist but has not yet been collected.",
                        "np": "ठेक्का प्रदान अभिलेख हुन सक्छ तर अहिलेसम्म सङ्कलन गरिएको छैन।",
                    },
                    {
                        "en": "The procurement may have been cancelled or re-tendered.",
                        "np": "खरिद रद्द भएको वा पुनः बोलपत्र गरिएको हुन सक्छ।",
                    },
                ],
                "recommendation_en": "Locate the award notice or agreement before drawing conclusions about the contractor or contract value.",
                "recommendation_np": "ठेकेदार वा ठेक्का रकमबारे निष्कर्ष निकाल्नुअघि ठेक्का प्रदान सूचना वा सम्झौता खोज्नुहोस्।",
                "source_references": procurement_sources,
            }
        )

    if tenders and not payments:
        payloads.append(
            {
                "rule_id": "EVIDENCE_PAYMENT_MISSING",
                "severity": AnomalyFlag.Severity.LOW,
                "reliability": AnomalyFlag.Reliability.MODERATE,
                "title_en": "Payment evidence has not been reported",
                "title_np": "भुक्तानी प्रमाण रिपोर्ट गरिएको छैन",
                "reason_en": "Procurement evidence exists, but no payment record is available in Budget Darpan.",
                "reason_np": "खरिद प्रमाण उपलब्ध छ तर बजेट दर्पणमा भुक्तानी अभिलेख छैन।",
                "data_used": {"tender_count": len(tenders), "payment_count": 0},
                "threshold": {"tender_count_min": 1, "payment_count": 0},
                "calculated_values": {},
                "possible_explanations": [
                    {
                        "en": "Payments may not yet have occurred.",
                        "np": "भुक्तानी अझै नभएको हुन सक्छ।",
                    },
                    {
                        "en": "Payment records may not yet be publicly available or collected.",
                        "np": "भुक्तानी अभिलेख अझै सार्वजनिक नभएको वा सङ्कलन नगरिएको हुन सक्छ।",
                    },
                ],
                "recommendation_en": "Request payment certificates or expenditure records and retain the current value as unknown until verified.",
                "recommendation_np": "भुक्तानी प्रमाणपत्र वा खर्च अभिलेख खोज्नुहोस् र प्रमाणित नभएसम्म रकम अज्ञात राख्नुहोस्।",
                "source_references": procurement_sources,
            }
        )

    if (
        project.official_progress_percent is None
        and not project.milestones.exists()
        and (project.status != Project.Status.UNKNOWN or monitoring_event)
    ):
        payloads.append(
            {
                "rule_id": "IMPLEMENTATION_PROGRESS_PERCENT_MISSING",
                "severity": AnomalyFlag.Severity.INFO,
                "reliability": AnomalyFlag.Reliability.OFFICIAL_REFERENCE,
                "title_en": "Implementation activity is recorded without numeric progress",
                "title_np": "कार्यान्वयन गतिविधि अभिलेख छ तर सङ्ख्यात्मक प्रगति उपलब्ध छैन",
                "reason_en": "The project is recorded as under implementation or monitored, but no physical-progress percentage, completed quantity, or milestone is linked.",
                "reason_np": "आयोजना कार्यान्वयन वा अनुगमनमा रहेको अभिलेख छ तर भौतिक प्रगति प्रतिशत, सम्पन्न परिमाण वा उपलब्धि जोडिएको छैन।",
                "data_used": {
                    "project_status": project.status,
                    "monitoring_date_bs": (monitoring_event.date_bs if monitoring_event else None),
                    "official_progress": None,
                    "milestone_count": 0,
                },
                "threshold": {
                    "implementation_or_monitoring_recorded": True,
                    "progress_measure_required": True,
                },
                "calculated_values": {},
                "possible_explanations": [
                    {
                        "en": "The monitoring record may confirm a visit without publishing measured completion.",
                        "np": "अनुगमन अभिलेखले स्थलगत भ्रमण पुष्टि गरे पनि नापिएको सम्पन्नता प्रकाशित नगरेको हुन सक्छ।",
                    },
                    {
                        "en": "A measurement book or completion certificate may exist outside the collected dataset.",
                        "np": "नापी किताब वा कार्यसम्पन्न प्रमाणपत्र सङ्कलित तथ्यबाहिर हुन सक्छ।",
                    },
                ],
                "recommendation_en": "Collect a monitoring report, measurement book, or completion certificate with measured physical progress.",
                "recommendation_np": "नापिएको भौतिक प्रगतिसहित अनुगमन प्रतिवेदन, नापी किताब वा कार्यसम्पन्न प्रमाणपत्र सङ्कलन गर्नुहोस्।",
                "source_references": progress_sources,
            }
        )
    elif project.official_progress_percent is None and not project.milestones.exists():
        payloads.append(
            {
                "rule_id": "EVIDENCE_PROGRESS_MISSING",
                "severity": AnomalyFlag.Severity.INFO,
                "reliability": AnomalyFlag.Reliability.STRONG,
                "title_en": "Official progress evidence is missing",
                "title_np": "आधिकारिक प्रगति प्रमाण उपलब्ध छैन",
                "reason_en": "No official completion percentage or project milestone is recorded.",
                "reason_np": "आधिकारिक सम्पन्न प्रतिशत वा आयोजना उपलब्धि अभिलेख गरिएको छैन।",
                "data_used": {"official_progress": None, "milestone_count": 0},
                "threshold": {"required_progress_or_milestone": True},
                "calculated_values": {},
                "possible_explanations": [
                    {
                        "en": "Progress reporting may be delayed or held in an uncollected record.",
                        "np": "प्रगति प्रतिवेदन ढिला भएको वा सङ्कलन नगरिएको अभिलेखमा हुन सक्छ।",
                    }
                ],
                "recommendation_en": "Collect an engineering progress report, measurement book, or completion certificate.",
                "recommendation_np": "इन्जिनियरिङ प्रगति प्रतिवेदन, नापी किताब वा सम्पन्न प्रमाणपत्र सङ्कलन गर्नुहोस्।",
                "source_references": [],
            }
        )

    contracted_total = sum((award.contract_amount for award in awards), Decimal("0"))
    paid_total = sum((payment.amount for payment in payments), Decimal("0"))
    if contracted_total > 0 and payments and project.official_progress_percent is not None:
        payment_percent = (paid_total / contracted_total * Decimal("100")).quantize(Decimal("0.01"))
        progress_percent = Decimal(project.official_progress_percent)
        percentage_point_gap = (payment_percent - progress_percent).quantize(Decimal("0.01"))
        if percentage_point_gap >= Decimal("15.00"):
            payloads.append(
                {
                    "rule_id": "PAYMENT_PROGRESS_MISMATCH",
                    "severity": AnomalyFlag.Severity.MEDIUM,
                    "reliability": (
                        AnomalyFlag.Reliability.MODERATE
                        if project.data_classification == "synthetic_demo"
                        else AnomalyFlag.Reliability.STRONG
                    ),
                    "title_en": "Reported payments are ahead of physical progress",
                    "title_np": "प्रतिवेदित भुक्तानी भौतिक प्रगतिभन्दा अगाडि छ",
                    "reason_en": (
                        f"Reported payments equal {payment_percent}% of the contract while "
                        f"reported physical progress is {progress_percent}%, a "
                        f"{percentage_point_gap} percentage-point gap."
                    ),
                    "reason_np": (
                        f"प्रतिवेदित भुक्तानी ठेक्का रकमको {payment_percent}% छ तर भौतिक प्रगति "
                        f"{progress_percent}% छ, अर्थात् {percentage_point_gap} प्रतिशत-बिन्दुको अन्तर।"
                    ),
                    "data_used": {
                        "contract_amount": str(contracted_total),
                        "reported_paid_amount": str(paid_total),
                        "reported_progress_percent": str(progress_percent),
                        "data_classification": project.data_classification,
                    },
                    "threshold": {"payment_ahead_of_progress_percentage_points_min": "15.00"},
                    "calculated_values": {
                        "payment_percent_of_contract": str(payment_percent),
                        "payment_progress_gap_percentage_points": str(percentage_point_gap),
                    },
                    "possible_explanations": [
                        {
                            "en": "Mobilization payments or stored materials may be paid before equivalent visible physical progress.",
                            "np": "परिचालन पेश्की वा भण्डारण गरिएको सामग्रीको भुक्तानी समान देखिने भौतिक प्रगतिभन्दा अघि भएको हुन सक्छ।",
                        },
                        {
                            "en": "The progress report and payment ledger may use different reporting dates.",
                            "np": "प्रगति प्रतिवेदन र भुक्तानी खाताले फरक प्रतिवेदन मिति प्रयोग गरेका हुन सक्छन्।",
                        },
                    ],
                    "recommendation_en": "Compare the latest payment certificates with the measurement book and a same-date engineering progress report.",
                    "recommendation_np": "पछिल्लो भुक्तानी प्रमाणपत्रलाई नापी किताब र सोही मितिको इन्जिनियरिङ प्रगति प्रतिवेदनसँग तुलना गर्नुहोस्।",
                    "source_references": _references(
                        project, ProjectDocumentLink.Relationship.PAYMENT
                    )
                    + progress_sources,
                }
            )

    if contracted_total > 0 and paid_total > contracted_total:
        excess = paid_total - contracted_total
        payloads.append(
            {
                "rule_id": "PAYMENTS_EXCEED_CONTRACT",
                "severity": AnomalyFlag.Severity.HIGH,
                "reliability": AnomalyFlag.Reliability.STRONG,
                "title_en": "Reported payments exceed the contract amount",
                "title_np": "प्रतिवेदित भुक्तानी ठेक्का रकमभन्दा बढी छ",
                "reason_en": (
                    f"Reported payments total NPR {paid_total} against a contract amount of "
                    f"NPR {contracted_total}."
                ),
                "reason_np": (
                    f"प्रतिवेदित भुक्तानी जम्मा रु. {paid_total} छ भने ठेक्का रकम रु. {contracted_total} छ।"
                ),
                "data_used": {
                    "contract_amount": str(contracted_total),
                    "reported_paid_amount": str(paid_total),
                },
                "threshold": {"reported_paid_must_not_exceed_contract": True},
                "calculated_values": {"amount_above_contract": str(excess)},
                "possible_explanations": [
                    {
                        "en": "A contract variation may not yet be linked, or a payment may be duplicated or assigned to the wrong contract.",
                        "np": "ठेक्का भेरिएसन अझै नजोडिएको, भुक्तानी दोहोरिएको वा गलत ठेक्कामा जोडिएको हुन सक्छ।",
                    }
                ],
                "recommendation_en": "Verify contract variations and reconcile every payment reference before drawing a conclusion.",
                "recommendation_np": "निष्कर्ष निकाल्नुअघि ठेक्का भेरिएसन जाँच गरी प्रत्येक भुक्तानी सन्दर्भ मिलान गर्नुहोस्।",
                "source_references": _references(project, ProjectDocumentLink.Relationship.PAYMENT)
                + procurement_sources,
            }
        )

    estimates = [tender.estimated_amount for tender in tenders if tender.estimated_amount]
    if project.allocated_amount is not None and estimates:
        largest_estimate = max(estimates)
        ratio = largest_estimate / project.allocated_amount if project.allocated_amount else None
        if ratio is not None and ratio >= Decimal("2"):
            payloads.append(
                {
                    "rule_id": "LINKED_SCOPE_AMOUNT_GAP",
                    "severity": AnomalyFlag.Severity.MEDIUM,
                    "reliability": AnomalyFlag.Reliability.LIMITED,
                    "title_en": "Linked allocation and tender estimate differ substantially",
                    "title_np": "जोडिएको विनियोजन र बोलपत्र अनुमानमा ठूलो अन्तर छ",
                    "reason_en": "The largest linked tender estimate is at least twice the available project allocation, but the records may cover different scopes or packages.",
                    "reason_np": "सबैभन्दा ठूलो जोडिएको बोलपत्र अनुमान उपलब्ध विनियोजनभन्दा कम्तीमा दोब्बर छ, तर अभिलेखले फरक कार्यक्षेत्र समेट्न सक्छ।",
                    "data_used": {
                        "allocated_amount": str(project.allocated_amount),
                        "largest_tender_estimate": str(largest_estimate),
                    },
                    "threshold": {"ratio_min": "2.00"},
                    "calculated_values": {"estimate_to_allocation_ratio": f"{ratio:.2f}"},
                    "possible_explanations": [
                        {
                            "en": "The budget line may fund only part of a larger tender.",
                            "np": "बजेट शीर्षकले ठूलो बोलपत्रको केही भाग मात्र वित्तपोषण गरेको हुन सक्छ।",
                        },
                        {
                            "en": "The records may refer to related but distinct project packages.",
                            "np": "अभिलेखहरू सम्बन्धित तर फरक आयोजना प्याकेजका हुन सक्छन्।",
                        },
                    ],
                    "recommendation_en": "Verify project scope, continuity, and funding sources before treating these amounts as directly comparable.",
                    "recommendation_np": "यी रकम प्रत्यक्ष तुलना गर्नुअघि आयोजनाको कार्यक्षेत्र, निरन्तरता र वित्तीय स्रोत प्रमाणित गर्नुहोस्।",
                    "source_references": _references(
                        project, ProjectDocumentLink.Relationship.ALLOCATION
                    )
                    + procurement_sources,
                }
            )

    if audit_sources:
        payloads.append(
            {
                "rule_id": "OFFICIAL_AUDIT_REFERENCE_REVIEW",
                "severity": AnomalyFlag.Severity.MEDIUM,
                "reliability": AnomalyFlag.Reliability.OFFICIAL_REFERENCE,
                "title_en": "Official audit evidence requires review",
                "title_np": "आधिकारिक लेखापरीक्षण प्रमाण समीक्षा आवश्यक",
                "reason_en": "An official audit source is linked to this evidence cluster. Its exact relationship and amounts must be reviewed before aggregation.",
                "reason_np": "यस प्रमाण समूहसँग आधिकारिक लेखापरीक्षण स्रोत जोडिएको छ। रकम जोड्नुअघि यसको ठ्याक्कै सम्बन्ध समीक्षा गर्नुपर्छ।",
                "data_used": {"audit_reference_count": len(audit_sources)},
                "threshold": {"audit_reference_count_min": 1},
                "calculated_values": {},
                "possible_explanations": [
                    {
                        "en": "The audit ledger rows may represent an advance and its settlement rather than separate spending.",
                        "np": "लेखापरीक्षणका पङ्क्तिले छुट्टै खर्चभन्दा पेश्की र त्यसको फर्छ्यौट जनाउन सक्छन्।",
                    }
                ],
                "recommendation_en": "Open the cited audit page and verify the ledger meaning with supporting project records.",
                "recommendation_np": "उद्धृत लेखापरीक्षण पृष्ठ खोल्नुहोस् र सहायक आयोजना अभिलेखबाट खाताको अर्थ प्रमाणित गर्नुहोस्।",
                "source_references": audit_sources,
            }
        )
    return payloads


@transaction.atomic
def evaluate_project(project):
    payloads = _rule_payloads(project)
    active_rule_ids = {payload["rule_id"] for payload in payloads}
    flags = []
    for payload in payloads:
        flag, _ = AnomalyFlag.objects.update_or_create(
            project=project,
            rule_id=payload.pop("rule_id"),
            defaults={**payload, "status": AnomalyFlag.Status.ACTIVE, "resolved_at": None},
        )
        flags.append(flag)
    AnomalyFlag.objects.filter(project=project, status=AnomalyFlag.Status.ACTIVE).exclude(
        rule_id__in=active_rule_ids
    ).update(status=AnomalyFlag.Status.RESOLVED, resolved_at=timezone.now())
    return flags


def evaluate_all_projects():
    return [flag for project in Project.objects.all() for flag in evaluate_project(project)]
