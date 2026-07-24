from decimal import ROUND_HALF_UP, Decimal

from budgets.models import BudgetAllocation


def _money(value):
    return f"{value:.2f}" if value is not None else None


def _utilization_percent(allocated_amount, spent_amount):
    if not allocated_amount or spent_amount is None:
        return None
    percent = (spent_amount / allocated_amount * Decimal("100")).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )
    return f"{percent:.2f}"


def reviewed_budget_comparison_queryset():
    return BudgetAllocation.objects.filter(
        budget_type=BudgetAllocation.BudgetType.TOTAL,
        review_status=BudgetAllocation.ReviewStatus.REVIEWED,
        spent_amount__isnull=False,
        source_document__isnull=False,
        source_page__isnull=False,
    ).select_related(
        "local_government",
        "fiscal_year",
        "subsector__sector",
        "source_document",
    )


def get_reviewed_budget_comparison(*, fiscal_year_code="", sector_code="", municipalities=None):
    queryset = reviewed_budget_comparison_queryset()
    if fiscal_year_code:
        queryset = queryset.filter(fiscal_year__code=fiscal_year_code)
    else:
        latest_code = (
            queryset.order_by("-fiscal_year__code")
            .values_list("fiscal_year__code", flat=True)
            .first()
        )
        if latest_code:
            queryset = queryset.filter(fiscal_year__code=latest_code)

    if sector_code:
        queryset = queryset.filter(subsector__sector__code=sector_code)
    if municipalities:
        queryset = queryset.filter(local_government__code__in=municipalities)

    allocations = list(
        queryset.order_by(
            "subsector__sector__name_en",
            "local_government__name_en",
        )
    )
    fiscal_year = allocations[0].fiscal_year if allocations else None
    records = []
    for allocation in allocations:
        document = allocation.source_document
        records.append(
            {
                "id": allocation.id,
                "local_government_code": allocation.local_government.code,
                "local_government_name_en": allocation.local_government.name_en,
                "local_government_name_np": allocation.local_government.name_np,
                "sector_code": allocation.subsector.sector.code,
                "sector_name_en": allocation.subsector.sector.name_en,
                "sector_name_np": allocation.subsector.sector.name_np,
                "allocated_amount": _money(allocation.allocated_amount),
                "spent_amount": _money(allocation.spent_amount),
                "utilization_percent": _utilization_percent(
                    allocation.allocated_amount,
                    allocation.spent_amount,
                ),
                "review_status": allocation.review_status,
                "reliability": allocation.reliability,
                "comparability": allocation.comparability,
                "source_scope_en": allocation.source_scope_en,
                "source_scope_np": allocation.source_scope_np,
                "data_classification": allocation.data_classification,
                "citation": {
                    "document_id": str(document.id),
                    "document_title": document.title_en,
                    "document_title_np": document.title_np,
                    "page": allocation.source_page,
                    "section": allocation.subsector.sector.name_en,
                    "source_url": document.source_url,
                },
            }
        )

    return {
        "fiscal_year": (
            {
                "id": fiscal_year.id,
                "code": fiscal_year.code,
                "year_bs": fiscal_year.year_bs,
                "year_ad": fiscal_year.year_ad,
                "label_np": fiscal_year.label_np,
            }
            if fiscal_year
            else None
        ),
        "currency": "NPR",
        "records": records,
        "evidence_summary": {
            "record_count": len(records),
            "municipality_count": len({record["local_government_code"] for record in records}),
            "sector_count": len({record["sector_code"] for record in records}),
            "reviewed_only": True,
            "note_en": (
                "Only human-reviewed values with a registered document and page citation are "
                "included. Scope warnings remain attached to each row."
            ),
            "note_np": (
                "दर्ता गरिएको कागजात र पृष्ठ उद्धरणसहित मानवद्वारा समीक्षा गरिएका मान मात्र "
                "समावेश छन्। प्रत्येक पङ्क्तिमा कार्यक्षेत्रसम्बन्धी चेतावनी राखिएको छ।"
            ),
        },
    }
