from decimal import Decimal

from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from payments.models import Payment

from projects.models import Project, ProjectMilestone


def _money(value):
    return f"{value:.2f}" if value is not None else None


def project_money_trail_queryset():
    payment_queryset = Payment.objects.select_related("milestone").order_by("paid_on", "reference")
    return Project.objects.select_related(
        "local_government__district__province",
        "ward",
        "fiscal_year",
        "subsector__sector",
        "budget_allocation",
        "location",
    ).prefetch_related(
        Prefetch("milestones", queryset=ProjectMilestone.objects.order_by("sequence")),
        "tenders__award__contractor",
        Prefetch("tenders__award__payments", queryset=payment_queryset),
    )


def get_project_money_trail(project_id):
    project = get_object_or_404(project_money_trail_queryset(), pk=project_id)
    tenders = list(project.tenders.all())
    procurement_items = []
    payments = []
    contract_amounts = []

    for tender in tenders:
        award = getattr(tender, "award", None)
        award_payload = None
        if award:
            contract_amounts.append(award.contract_amount)
            award_payments = list(award.payments.all())
            payments.extend(award_payments)
            award_payload = {
                "reference": award.award_reference,
                "contract_amount": _money(award.contract_amount),
                "awarded_date": award.awarded_date,
                "contract_start_date": award.contract_start_date,
                "contract_end_date": award.contract_end_date,
                "contractor": {
                    "name": award.contractor.name,
                    "registration_number": award.contractor.registration_number,
                    "municipality_name": award.contractor.municipality_name,
                    "data_classification": award.contractor.data_classification,
                },
                "source_url": award.source_url,
                "data_classification": award.data_classification,
            }

        procurement_items.append(
            {
                "reference": tender.reference,
                "invitation_number": tender.invitation_number,
                "title_en": tender.title_en,
                "title_np": tender.title_np,
                "procurement_method": tender.procurement_method,
                "published_date": tender.published_date,
                "bid_submission_deadline": tender.bid_submission_deadline,
                "estimated_amount": _money(tender.estimated_amount),
                "bid_security_amount": _money(tender.bid_security_amount),
                "data_note_en": tender.data_note_en,
                "data_note_np": tender.data_note_np,
                "source_url": tender.source_url,
                "data_classification": tender.data_classification,
                "award": award_payload,
            }
        )

    contracted_amount = sum(contract_amounts, Decimal("0")) if contract_amounts else None
    reported_paid_amount = (
        sum((item.amount for item in payments), Decimal("0")) if payments else None
    )
    reported_balance = (
        contracted_amount - reported_paid_amount
        if contracted_amount is not None and reported_paid_amount is not None
        else None
    )

    location = getattr(project, "location", None)
    payment_items = [
        {
            "reference": payment.reference,
            "amount": _money(payment.amount),
            "paid_on": payment.paid_on,
            "description_en": payment.description_en,
            "description_np": payment.description_np,
            "milestone_sequence": payment.milestone.sequence if payment.milestone else None,
            "source_url": payment.source_url,
            "data_classification": payment.data_classification,
        }
        for payment in sorted(payments, key=lambda item: (item.paid_on, item.reference))
    ]

    return {
        "project": {
            "id": project.id,
            "code": project.code,
            "title_en": project.title_en,
            "title_np": project.title_np,
            "description_en": project.description_en,
            "description_np": project.description_np,
            "status": project.status,
            "official_progress_percent": project.official_progress_percent,
            "planned_start_date": project.planned_start_date,
            "planned_end_date": project.planned_end_date,
            "data_classification": project.data_classification,
            "data_note_en": project.data_note_en,
            "data_note_np": project.data_note_np,
            "source_url": project.source_url,
            "local_government": {
                "code": project.local_government.code,
                "name_en": project.local_government.name_en,
                "name_np": project.local_government.name_np,
            },
            "ward_number": project.ward.number if project.ward else None,
            "fiscal_year": {
                "code": project.fiscal_year.code,
                "year_bs": project.fiscal_year.year_bs,
                "year_ad": project.fiscal_year.year_ad,
                "label_np": project.fiscal_year.label_np,
            },
            "sector": {
                "code": project.subsector.sector.code,
                "name_en": project.subsector.sector.name_en,
                "name_np": project.subsector.sector.name_np,
            },
            "subsector": {
                "code": project.subsector.code,
                "name_en": project.subsector.name_en,
                "name_np": project.subsector.name_np,
            },
            "location": (
                {
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "label_en": location.label_en,
                    "label_np": location.label_np,
                }
                if location
                else None
            ),
        },
        "financial_summary": {
            "allocated_amount": _money(project.allocated_amount),
            "contracted_amount": _money(contracted_amount),
            "reported_paid_amount": _money(reported_paid_amount),
            "reported_contract_balance": _money(reported_balance),
            "payment_reporting_status": "reported" if payments else "not_yet_reported",
            "currency": "NPR",
        },
        "procurement": procurement_items,
        "payments": payment_items,
        "milestones": [
            {
                "sequence": milestone.sequence,
                "title_en": milestone.title_en,
                "title_np": milestone.title_np,
                "status": milestone.status,
                "progress_percent": milestone.progress_percent,
                "planned_date": milestone.planned_date,
                "completed_date": milestone.completed_date,
            }
            for milestone in project.milestones.all()
        ],
    }
