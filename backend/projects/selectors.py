from decimal import Decimal

from django.db.models import Count, Exists, OuterRef, Prefetch, Q, Sum
from django.shortcuts import get_object_or_404
from payments.models import Payment

from projects.models import Project, ProjectEvidenceEvent, ProjectMilestone


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
        Prefetch(
            "evidence_events",
            queryset=ProjectEvidenceEvent.objects.order_by("source_page", "event_type", "date_bs"),
        ),
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
    evidence_events = list(project.evidence_events.all())
    events_by_type = {}
    for event in evidence_events:
        events_by_type.setdefault(event.event_type, event)
    agreement_event = events_by_type.get(ProjectEvidenceEvent.EventType.AGREEMENT_RECORDED)
    monitoring_event = events_by_type.get(ProjectEvidenceEvent.EventType.MONITORING_RECORDED)
    payment_date_event = events_by_type.get(ProjectEvidenceEvent.EventType.PAYMENT_DATE_RECORDED)
    payment_reporting_status = (
        "reported"
        if payments
        else "date_reported_amount_missing"
        if payment_date_event
        else "not_yet_reported"
    )
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
            "payment_reporting_status": payment_reporting_status,
            "currency": "NPR",
        },
        "evidence_coverage": {
            "allocation": {
                "status": (
                    "amount_reported" if project.allocated_amount is not None else "not_found"
                ),
                "amount": _money(project.allocated_amount),
            },
            "agreement": {
                "status": "date_reported" if agreement_event else "not_found",
                "date_bs": agreement_event.date_bs if agreement_event else None,
            },
            "monitoring": {
                "status": "date_reported" if monitoring_event else "not_found",
                "date_bs": monitoring_event.date_bs if monitoring_event else None,
            },
            "procurement": {
                "status": "notice_reported" if tenders else "not_found",
            },
            "contract_award": {
                "status": "award_reported" if contract_amounts else "not_found",
            },
            "payment": {
                "status": payment_reporting_status,
                "date_bs": payment_date_event.date_bs if payment_date_event else None,
                "amount": _money(reported_paid_amount),
            },
            "physical_progress": {
                "status": (
                    "percentage_reported"
                    if project.official_progress_percent is not None
                    else "status_reported_percentage_missing"
                    if project.status != Project.Status.UNKNOWN
                    else "not_found"
                ),
                "project_status": project.status,
                "percentage": project.official_progress_percent,
            },
        },
        "evidence_events": [
            {
                "event_type": event.event_type,
                "date_bs": event.date_bs,
                "date_ad": event.date_ad,
                "source_page": event.source_page,
                "source_url": event.source_url,
                "note_en": event.note_en,
                "note_np": event.note_np,
                "data_classification": event.data_classification,
            }
            for event in evidence_events
        ],
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


def get_project_discovery_summary(queryset):
    """Return filter-aware, structured project discovery aggregates.

    Financial totals intentionally exclude unknown values. Separate known and
    unknown counts keep the API from presenting missing data as zero.
    """
    from documents.models import ProjectDocumentLink
    from procurement.models import Tender

    filtered_ids = queryset.order_by().values("pk")
    projects = Project.objects.filter(pk__in=filtered_ids).annotate(
        has_evidence=Exists(ProjectDocumentLink.objects.filter(project_id=OuterRef("pk"))),
        has_procurement=Exists(Tender.objects.filter(project_id=OuterRef("pk"))),
        has_reported_payment=Exists(
            Payment.objects.filter(contract_award__tender__project_id=OuterRef("pk"))
        ),
    )

    totals = projects.aggregate(
        project_count=Count("pk"),
        known_allocation_count=Count(
            "pk",
            filter=Q(allocated_amount__isnull=False),
        ),
        allocated_total=Sum("allocated_amount"),
        evidence_project_count=Count("pk", filter=Q(has_evidence=True)),
        procurement_project_count=Count("pk", filter=Q(has_procurement=True)),
        payment_reported_project_count=Count(
            "pk",
            filter=Q(has_reported_payment=True),
        ),
        geolocated_project_count=Count("pk", filter=Q(location__isnull=False)),
    )
    project_count = totals["project_count"] or 0
    known_allocation_count = totals["known_allocation_count"] or 0

    fiscal_year_rows = (
        Project.objects.filter(pk__in=filtered_ids)
        .values(
            "fiscal_year__code",
            "fiscal_year__year_bs",
            "fiscal_year__year_ad",
        )
        .annotate(
            project_count=Count("pk"),
            known_allocation_count=Count(
                "pk",
                filter=Q(allocated_amount__isnull=False),
            ),
            allocated_total=Sum("allocated_amount"),
        )
        .order_by("-fiscal_year__code")
    )
    sector_rows = (
        Project.objects.filter(pk__in=filtered_ids)
        .values(
            "subsector__sector__code",
            "subsector__sector__name_en",
            "subsector__sector__name_np",
        )
        .annotate(
            project_count=Count("pk"),
            known_allocation_count=Count(
                "pk",
                filter=Q(allocated_amount__isnull=False),
            ),
            allocated_total=Sum("allocated_amount"),
        )
        .order_by("subsector__sector__name_en")
    )
    status_rows = (
        Project.objects.filter(pk__in=filtered_ids)
        .values("status")
        .annotate(project_count=Count("pk"))
        .order_by("status")
    )

    return {
        "totals": {
            "project_count": project_count,
            "known_allocation_count": known_allocation_count,
            "unknown_allocation_count": project_count - known_allocation_count,
            "allocated_total": _money(totals["allocated_total"]),
            "evidence_project_count": totals["evidence_project_count"] or 0,
            "procurement_project_count": totals["procurement_project_count"] or 0,
            "payment_reported_project_count": (totals["payment_reported_project_count"] or 0),
            "geolocated_project_count": totals["geolocated_project_count"] or 0,
            "currency": "NPR",
        },
        "by_fiscal_year": [
            {
                "code": row["fiscal_year__code"],
                "year_bs": row["fiscal_year__year_bs"],
                "year_ad": row["fiscal_year__year_ad"],
                "project_count": row["project_count"],
                "known_allocation_count": row["known_allocation_count"],
                "allocated_total": _money(row["allocated_total"]),
            }
            for row in fiscal_year_rows
        ],
        "by_sector": [
            {
                "code": row["subsector__sector__code"],
                "name_en": row["subsector__sector__name_en"],
                "name_np": row["subsector__sector__name_np"],
                "project_count": row["project_count"],
                "known_allocation_count": row["known_allocation_count"],
                "allocated_total": _money(row["allocated_total"]),
            }
            for row in sector_rows
        ],
        "by_status": [
            {
                "status": row["status"],
                "project_count": row["project_count"],
            }
            for row in status_rows
        ],
    }
