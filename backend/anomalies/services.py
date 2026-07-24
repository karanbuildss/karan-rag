# ruff: noqa: E501

from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from documents.models import ProjectDocumentLink
from projects.models import Project

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
    payloads = []

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

    if project.official_progress_percent is None and not project.milestones.exists():
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
