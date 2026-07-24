from projects.selectors import get_project_money_trail


def build_structured_facts(project):
    trail = get_project_money_trail(project.id)
    summary = trail["financial_summary"]
    procurement = []
    for tender in trail["procurement"]:
        award = tender["award"]
        procurement.append(
            {
                "reference": tender["reference"],
                "invitation_number": tender["invitation_number"],
                "title_en": tender["title_en"],
                "title_np": tender["title_np"],
                "estimated_amount": tender["estimated_amount"],
                "estimate_meaning": "tender_estimate_not_award_or_payment",
                "published_date": tender["published_date"],
                "bid_submission_deadline": tender["bid_submission_deadline"],
                "award_status": "reported" if award else "unknown",
                "award": award,
            }
        )

    unknown_fields = []
    if summary["contracted_amount"] is None:
        unknown_fields.extend(["contract_award", "winning_contractor", "contract_amount"])
    if summary["reported_paid_amount"] is None:
        unknown_fields.append("payments")
    if trail["project"]["official_progress_percent"] is None:
        unknown_fields.append("official_progress")
    if not trail["milestones"]:
        unknown_fields.append("milestones")
    if trail["project"]["location"] is None:
        unknown_fields.append("exact_location")

    return {
        "project": {
            "id": str(project.id),
            "code": project.code,
            "title_en": project.title_en,
            "title_np": project.title_np,
            "municipality_en": trail["project"]["local_government"]["name_en"],
            "municipality_np": trail["project"]["local_government"]["name_np"],
            "ward_number": trail["project"]["ward_number"],
            "fiscal_year": trail["project"]["fiscal_year"],
            "status": trail["project"]["status"],
            "data_classification": trail["project"]["data_classification"],
            "data_note_en": trail["project"]["data_note_en"],
            "data_note_np": trail["project"]["data_note_np"],
        },
        "budget": {
            "allocated_amount": summary["allocated_amount"],
            "currency": summary["currency"],
            "classification": trail["project"]["data_classification"],
        },
        "procurement": procurement,
        "contract": {
            "status": "reported" if summary["contracted_amount"] is not None else "unknown",
            "amount": summary["contracted_amount"],
        },
        "payments": {
            "status": summary["payment_reporting_status"],
            "reported_total": summary["reported_paid_amount"],
            "records": trail["payments"],
        },
        "progress": {
            "official_percent": trail["project"]["official_progress_percent"],
            "milestones": trail["milestones"],
        },
        "location": trail["project"]["location"],
        "unknown_fields": unknown_fields,
    }
