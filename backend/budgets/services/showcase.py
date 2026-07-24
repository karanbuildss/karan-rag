from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from config.models import DataClassification
from django.utils import timezone
from documents.models import DocumentPage, ProjectDocumentLink, SourceDocument
from payments.models import Payment
from procurement.models import ContractAward, Contractor, Tender
from projects.models import Project, ProjectLocation, ProjectMilestone

SHOWCASE_PROJECT_ID = UUID("e4d7eeb5-50f8-4a67-9c44-477d121f765d")
SHOWCASE_DOCUMENT_ID = UUID("5ca42695-8a90-4c2a-86e6-701c56bce32f")
SHOWCASE_PROJECT_CODE = "DEMO-PKR-W08-ROAD-2081-82"
SHOWCASE_SOURCE_URL = f"http://localhost:8000/api/v1/documents/{SHOWCASE_DOCUMENT_ID}/file/"
NEPAL_TIMEZONE = ZoneInfo("Asia/Kathmandu")


SHOWCASE_PAGES = {
    1: {
        "section": "Allocation and scope",
        "text": (
            "Synthetic showcase record. Pokhara Ward 8 climate-resilient road and drainage "
            "demonstration. Fiscal year 2081/82. Allocated amount NPR 10,000,000.00. The "
            "showcase scope covers drainage, road-base improvement, surfacing, accessibility, "
            "and handover. These values are realistic demonstration data, not an official claim."
        ),
    },
    2: {
        "section": "Tender and contract award",
        "text": (
            "Synthetic tender DEMO/PKR/NCB/W/081-82-01 used open competitive bidding. The "
            "estimate is NPR 9,600,000.00. A synthetic award of NPR 9,000,000.00 was recorded "
            "to Gandaki Civic Works JV (Synthetic) on 2024-08-15, with work scheduled from "
            "2024-09-01 to 2025-05-31."
        ),
    },
    3: {
        "section": "Payment certificates",
        "text": (
            "Synthetic payment certificate DEMO-PAY-001 records NPR 1,800,000.00 on "
            "2024-09-10. DEMO-PAY-002 records NPR 2,700,000.00 on 2024-12-20. "
            "DEMO-PAY-003 records NPR 2,700,000.00 on 2025-03-15. Total reported synthetic "
            "payments are NPR 7,200,000.00, equal to 80 percent of the contract amount."
        ),
    },
    4: {
        "section": "Physical progress and monitoring",
        "text": (
            "Synthetic monitoring dated 2025-03-20 reports 58 percent overall physical "
            "progress. Survey and drainage milestones are complete, road-base improvement is "
            "75 percent, surfacing is 35 percent, and handover has not started. Because payments "
            "are 80 percent while physical progress is 58 percent, review is recommended; this "
            "pattern alone is not proof of wrongdoing."
        ),
    },
}


def seed_synthetic_showcase(*, local_government, ward, fiscal_year, subsector):
    """Seed one complete, visibly synthetic trail without altering official projects."""
    project, _ = Project.objects.update_or_create(
        id=SHOWCASE_PROJECT_ID,
        defaults={
            "code": SHOWCASE_PROJECT_CODE,
            "local_government": local_government,
            "ward": ward,
            "fiscal_year": fiscal_year,
            "subsector": subsector,
            "budget_allocation": None,
            "title_en": "Pokhara Ward 8 Road Accountability Showcase (Synthetic)",
            "title_np": "पोखरा वडा ८ सडक जवाफदेहिता प्रदर्शन (कृत्रिम)",
            "description_en": (
                "A complete synthetic money trail used only to demonstrate how future official "
                "allocation, procurement, award, payment, progress, map, anomaly, and citizen "
                "evidence records will connect."
            ),
            "description_np": (
                "भविष्यमा आधिकारिक विनियोजन, खरिद, ठेक्का, भुक्तानी, प्रगति, नक्सा, विसंगति र "
                "नागरिक प्रमाण कसरी जोडिन्छ भन्ने देखाउन मात्र प्रयोग गरिएको पूर्ण कृत्रिम विवरण।"
            ),
            "status": Project.Status.IMPLEMENTATION,
            "allocated_amount": Decimal("10000000.00"),
            "official_progress_percent": Decimal("58.00"),
            "planned_start_date": date(2024, 9, 1),
            "planned_end_date": date(2025, 5, 31),
            "data_classification": DataClassification.SYNTHETIC_DEMO,
            "data_note_en": (
                "Every financial, contractor, payment, progress, milestone, and coordinate value "
                "on this showcase project is synthetic demo data and must be replaced with "
                "verified government records before production use."
            ),
            "data_note_np": (
                "यस प्रदर्शन आयोजनाका सबै वित्तीय, ठेकेदार, भुक्तानी, प्रगति, उपलब्धि र "
                "निर्देशाङ्क कृत्रिम नमुना हुन् र उत्पादन प्रयोगअघि प्रमाणित सरकारी अभिलेखले बदल्नुपर्छ।"
            ),
            "source_url": SHOWCASE_SOURCE_URL,
        },
    )
    project.full_clean()
    project.save()

    location, _ = ProjectLocation.objects.update_or_create(
        project=project,
        defaults={
            "latitude": Decimal("28.209600"),
            "longitude": Decimal("83.985600"),
            "label_en": "Synthetic demonstration marker near central Pokhara",
            "label_np": "पोखरा केन्द्र नजिकको कृत्रिम प्रदर्शन चिन्ह",
        },
    )
    location.full_clean()
    location.save()

    milestone_rows = [
        (1, "Survey and design", "सर्वेक्षण तथा डिजाइन", "completed", "100", date(2024, 9, 15)),
        (2, "Drainage construction", "नाली निर्माण", "completed", "100", date(2024, 12, 15)),
        (3, "Road-base improvement", "सडक आधार सुधार", "in_progress", "75", None),
        (4, "Surface and accessibility works", "सतह तथा पहुँचयोग्यता कार्य", "in_progress", "35", None),
        (5, "Inspection and handover", "निरीक्षण तथा हस्तान्तरण", "not_started", "0", None),
    ]
    milestones = {}
    for sequence, title_en, title_np, status, progress, completed_date in milestone_rows:
        milestone, _ = ProjectMilestone.objects.update_or_create(
            project=project,
            sequence=sequence,
            defaults={
                "title_en": title_en,
                "title_np": title_np,
                "status": status,
                "progress_percent": Decimal(progress),
                "planned_date": date(2024, 9, 15) if sequence == 1 else None,
                "completed_date": completed_date,
            },
        )
        milestone.full_clean()
        milestone.save()
        milestones[sequence] = milestone

    contractor, _ = Contractor.objects.update_or_create(
        registration_number="SYNTH-DEMO-PKR-001",
        defaults={
            "name": "Gandaki Civic Works JV (Synthetic)",
            "municipality_name": "Pokhara",
            "data_classification": DataClassification.SYNTHETIC_DEMO,
        },
    )
    tender, _ = Tender.objects.update_or_create(
        reference="DEMO/PKR/NCB/W/081-82-01",
        defaults={
            "project": project,
            "invitation_number": "DEMO-IFB-081-82-01",
            "title_en": "Pokhara Ward 8 road and drainage showcase (Synthetic)",
            "title_np": "पोखरा वडा ८ सडक तथा नाली प्रदर्शन (कृत्रिम)",
            "procurement_method": Tender.ProcurementMethod.OPEN,
            "published_date": date(2024, 7, 1),
            "bid_submission_deadline": datetime(2024, 8, 1, 12, 0, tzinfo=NEPAL_TIMEZONE),
            "estimated_amount": Decimal("9600000.00"),
            "bid_security_amount": Decimal("275000.00"),
            "data_note_en": "Synthetic procurement used only for the end-to-end showcase.",
            "data_note_np": "अन्त्यदेखि अन्त्य प्रदर्शनका लागि मात्र प्रयोग गरिएको कृत्रिम खरिद।",
            "source_url": SHOWCASE_SOURCE_URL,
            "data_classification": DataClassification.SYNTHETIC_DEMO,
        },
    )
    tender.full_clean()
    tender.save()

    award, _ = ContractAward.objects.update_or_create(
        tender=tender,
        defaults={
            "contractor": contractor,
            "award_reference": "DEMO-AWARD-081-82-01",
            "contract_amount": Decimal("9000000.00"),
            "awarded_date": date(2024, 8, 15),
            "contract_start_date": date(2024, 9, 1),
            "contract_end_date": date(2025, 5, 31),
            "source_url": SHOWCASE_SOURCE_URL,
            "data_classification": DataClassification.SYNTHETIC_DEMO,
        },
    )
    award.full_clean()
    award.save()

    payment_rows = [
        ("DEMO-PAY-001", "1800000.00", date(2024, 9, 10), 1, "Mobilization payment"),
        ("DEMO-PAY-002", "2700000.00", date(2024, 12, 20), 2, "First interim certificate"),
        ("DEMO-PAY-003", "2700000.00", date(2025, 3, 15), 4, "Second interim certificate"),
    ]
    for reference, amount, paid_on, milestone_sequence, description in payment_rows:
        payment, _ = Payment.objects.update_or_create(
            reference=reference,
            defaults={
                "contract_award": award,
                "milestone": milestones[milestone_sequence],
                "amount": Decimal(amount),
                "paid_on": paid_on,
                "description_en": f"{description} (synthetic demo)",
                "description_np": "कृत्रिम प्रदर्शन भुक्तानी",
                "source_url": SHOWCASE_SOURCE_URL,
                "data_classification": DataClassification.SYNTHETIC_DEMO,
            },
        )
        payment.full_clean()
        payment.save()

    document, _ = SourceDocument.objects.update_or_create(
        id=SHOWCASE_DOCUMENT_ID,
        defaults={
            "title_en": "Budget Darpan Complete Money Trail Showcase (Synthetic)",
            "title_np": "बजेट दर्पण पूर्ण रकम यात्रा प्रदर्शन (कृत्रिम)",
            "document_type": SourceDocument.DocumentType.OTHER,
            "local_government": local_government,
            "fiscal_year": fiscal_year,
            "language": SourceDocument.Language.MIXED,
            "file_format": SourceDocument.FileFormat.PDF,
            "original_filename": "budget-darpan-synthetic-showcase.pdf",
            "sha256": "",
            "source_url": SHOWCASE_SOURCE_URL,
            "source_url_kind": SourceDocument.SourceUrlKind.DIRECT_PDF,
            "source_note": (
                "Generated synthetic evidence for the hackathon showcase; not an official "
                "government document."
            ),
            "data_classification": DataClassification.SYNTHETIC_DEMO,
            "processing_status": SourceDocument.ProcessingStatus.APPROVED,
            "page_count": len(SHOWCASE_PAGES),
            "extraction_error": "",
            "extracted_at": timezone.now(),
        },
    )
    document.full_clean()
    document.save()

    for page_number, page_payload in SHOWCASE_PAGES.items():
        page, _ = DocumentPage.objects.update_or_create(
            document=document,
            page_number=page_number,
            defaults={
                "section": page_payload["section"],
                "extracted_text": page_payload["text"],
                "extraction_method": DocumentPage.ExtractionMethod.EMBEDDED_TEXT,
                "text_quality_score": Decimal("1.0000"),
                "review_status": DocumentPage.ReviewStatus.APPROVED,
                "extraction_warnings": ["synthetic_demo_content"],
                "character_count": len(page_payload["text"]),
            },
        )
        page.full_clean()
        page.save()

    link_rows = [
        (ProjectDocumentLink.Relationship.ALLOCATION, 1, "Synthetic allocation and scope"),
        (ProjectDocumentLink.Relationship.PROCUREMENT, 2, "Synthetic tender and award"),
        (ProjectDocumentLink.Relationship.PAYMENT, 3, "Synthetic payment certificates"),
        (ProjectDocumentLink.Relationship.PROGRESS, 4, "Synthetic physical progress"),
    ]
    for relationship, page_number, section in link_rows:
        link, _ = ProjectDocumentLink.objects.update_or_create(
            project=project,
            document=document,
            relationship=relationship,
            defaults={
                "page_from": page_number,
                "page_to": page_number,
                "section": section,
                "evidence_note_en": (
                    "Synthetic showcase evidence. Replace this row with an official record in "
                    "a production deployment."
                ),
                "evidence_note_np": (
                    "कृत्रिम प्रदर्शन प्रमाण। उत्पादन प्रयोगमा यसलाई आधिकारिक अभिलेखले बदल्नुहोस्।"
                ),
            },
        )
        link.full_clean()
        link.save()

    return project
