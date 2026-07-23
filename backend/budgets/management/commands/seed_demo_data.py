from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from config.models import DataClassification
from django.core.management.base import BaseCommand
from django.db import transaction
from geography.models import District, LocalGovernment, Province, Ward
from payments.models import Payment
from procurement.models import Contractor, Tender
from projects.models import Project

from budgets.models import BudgetAllocation, FiscalYear, Sector, SubSector

REAL_PROJECT_ID = UUID("6f3ef140-e6b9-4d6b-915f-74080c804208")
FOLLOW_UP_PROJECT_ID = UUID("2fb7eb1c-8b5a-4df8-9737-5c2dbb5399c4")
FOOTPATH_PROJECT_ID = UUID("b625763a-39c5-4af2-a0e8-eaef138ddb7c")
# Retained as a compatibility alias for the existing route and downstream imports.
DEMO_PROJECT_ID = REAL_PROJECT_ID

POKHARA_BUDGET_SOURCE = "https://pokharamun.gov.np/budget-program?field_fiscal_year_tid=All"
BOLPATRA_SOURCE = "https://bolpatra.gov.np/egp/searchOpportunity"
NEPAL_TIMEZONE = ZoneInfo("Asia/Kathmandu")


class Command(BaseCommand):
    help = "Seed the evidence-backed Pokhara Ward 8 Jalpa Marg showcase project."

    @transaction.atomic
    def handle(self, *args, **options):
        classification = DataClassification.RECONSTRUCTED

        province, _ = Province.objects.update_or_create(
            code="P4",
            defaults={"name_en": "Gandaki Province", "name_np": "गण्डकी प्रदेश"},
        )
        district, _ = District.objects.update_or_create(
            code="KSK",
            defaults={
                "province": province,
                "name_en": "Kaski",
                "name_np": "कास्की",
            },
        )
        local_government, _ = LocalGovernment.objects.update_or_create(
            code="PKR",
            defaults={
                "district": district,
                "name_en": "Pokhara Metropolitan City",
                "name_np": "पोखरा महानगरपालिका",
                "government_type": LocalGovernment.GovernmentType.METROPOLITAN,
            },
        )
        LocalGovernment.objects.update_or_create(
            code="RUPA",
            defaults={
                "district": district,
                "name_en": "Rupa Rural Municipality",
                "name_np": "रूपा गाउँपालिका",
                "government_type": LocalGovernment.GovernmentType.RURAL_MUNICIPALITY,
            },
        )
        ward, _ = Ward.objects.update_or_create(
            local_government=local_government,
            number=8,
            defaults={"name_en": "Ward 8", "name_np": "वडा नं. ८"},
        )

        fiscal_year_rows = [
            ("2077-78", "2077/78", "2020/21", "आर्थिक वर्ष २०७७/७८"),
            ("2078-79", "2078/79", "2021/22", "आर्थिक वर्ष २०७८/७९"),
            ("2079-80", "2079/80", "2022/23", "आर्थिक वर्ष २०७९/८०"),
            ("2080-81", "2080/81", "2023/24", "आर्थिक वर्ष २०८०/८१"),
            ("2081-82", "2081/82", "2024/25", "आर्थिक वर्ष २०८१/८२"),
            ("2082-83", "2082/83", "2025/26", "आर्थिक वर्ष २०८२/८३"),
        ]
        fiscal_years = {}
        for code, year_bs, year_ad, label_np in fiscal_year_rows:
            fiscal_years[code], _ = FiscalYear.objects.update_or_create(
                code=code,
                defaults={
                    "year_bs": year_bs,
                    "year_ad": year_ad,
                    "label_np": label_np,
                },
            )
        fiscal_year = fiscal_years["2077-78"]

        sector, _ = Sector.objects.update_or_create(
            code="INF",
            defaults={
                "name_en": "Infrastructure Development",
                "name_np": "पूर्वाधार विकास",
            },
        )
        subsector, _ = SubSector.objects.update_or_create(
            code="INF-ROAD",
            defaults={
                "sector": sector,
                "name_en": "Roads",
                "name_np": "सडक",
            },
        )

        # The red book records NPR 400,000 from internal revenue and NPR 400,000
        # from public participation. Exact spending is not present in the source.
        allocation, _ = BudgetAllocation.objects.update_or_create(
            local_government=local_government,
            fiscal_year=fiscal_year,
            subsector=subsector,
            budget_type=BudgetAllocation.BudgetType.CAPITAL,
            defaults={
                "allocated_amount": Decimal("800000.00"),
                "spent_amount": None,
                "data_classification": classification,
                "source_url": POKHARA_BUDGET_SOURCE,
            },
        )

        project, _ = Project.objects.update_or_create(
            id=REAL_PROJECT_ID,
            defaults={
                "code": "PKR-W08-JALPA-2077-78",
                "local_government": local_government,
                "ward": ward,
                "fiscal_year": fiscal_year,
                "subsector": subsector,
                "budget_allocation": allocation,
                "title_en": "Jalpa Marg Ward 8 Road Works",
                "title_np": "जाल्पा मार्ग वडा नं. ८ सडक कार्य",
                "description_en": (
                    "An evidence-backed reconstruction connecting the FY 2077/78 red-book "
                    "entry for Gyan Bahadur Jalpa Marg road construction with a probable "
                    "Jalpa Marg upgrading tender and a related Ward 8 drainage and "
                    "blacktopping entry in the official audit."
                ),
                "description_np": (
                    "आर्थिक वर्ष २०७७/७८ को रातो किताबमा रहेको ज्ञान बहादुर जाल्पा मार्ग सडक "
                    "निर्माण र आधिकारिक लेखापरीक्षणमा उल्लेखित वडा नं. ८ जाल्पा मार्ग नाला निर्माण "
                    "तथा कालोपत्रे विवरणलाई जोडेर पुनर्निर्माण गरिएको अभिलेख।"
                ),
                "status": Project.Status.UNKNOWN,
                "allocated_amount": Decimal("800000.00"),
                "official_progress_percent": None,
                "planned_start_date": None,
                "planned_end_date": None,
                "data_classification": classification,
                "data_note_en": (
                    "The FY 2077/78 tender is linked by road name, ward, and year. Its NPR "
                    "9,477,987.16 estimate is not a contract value and is not assumed to equal "
                    "the NPR 800,000 budget row. Award, payments, progress, and location "
                    "remain unknown."
                ),
                "data_note_np": (
                    "आर्थिक वर्ष २०७७/७८ को बोलपत्र सडकको नाम, वडा र वर्षका आधारमा जोडिएको हो। "
                    "यसको रु. ९४,७७,९८७.१६ अनुमान ठेक्का रकम होइन र रु. ८,००,००० बजेट पङ्क्तिसँग "
                    "बराबर मानिएको छैन। ठेक्का, भुक्तानी, प्रगति र स्थान अझै अज्ञात छन्।"
                ),
                "source_url": POKHARA_BUDGET_SOURCE,
            },
        )
        project.full_clean()
        project.save()

        # Remove the superseded synthetic trail. Unknown evidence must remain unknown.
        Payment.objects.filter(contract_award__tender__project=project).delete()
        project.tenders.all().delete()
        project.milestones.all().delete()
        if hasattr(project, "location"):
            project.location.delete()
        Contractor.objects.filter(
            registration_number="SYNTH-PKR-001",
            contract_awards__isnull=True,
        ).delete()
        BudgetAllocation.objects.filter(
            data_classification=DataClassification.SYNTHETIC_DEMO,
            projects__isnull=True,
        ).delete()

        later_project_rows = [
            {
                "id": FOLLOW_UP_PROJECT_ID,
                "code": "PKR-W08-JALPA-UPGRADE-2078-79",
                "fiscal_year": fiscal_years["2078-79"],
                "title_en": "Jalpa Marg Upgrading Procurement 2078/79",
                "title_np": "जाल्पा मार्ग स्तरोन्नति खरिद २०७८/७९",
                "description_en": (
                    "An official procurement record for a later Jalpa Marg upgrading package. "
                    "It remains separate from the FY 2077/78 evidence cluster because no "
                    "available document proves that it is a continuation or re-tender."
                ),
                "description_np": (
                    "जाल्पा मार्ग स्तरोन्नतिको पछिल्लो आधिकारिक खरिद अभिलेख। उपलब्ध कागजातले "
                    "यसलाई आर्थिक वर्ष २०७७/७८ को निरन्तरता वा पुनः बोलपत्र प्रमाणित नगरेकाले "
                    "छुट्टै राखिएको छ।"
                ),
                "data_note_en": (
                    "Only the procurement notice is available. Allocation, award, contractor, "
                    "payments, progress, completion, and exact location remain unknown."
                ),
                "data_note_np": (
                    "खरिद सूचना मात्र उपलब्ध छ। विनियोजन, ठेक्का, ठेकेदार, भुक्तानी, प्रगति, "
                    "सम्पन्नता र ठ्याक्कै स्थान अज्ञात छन्।"
                ),
            },
            {
                "id": FOOTPATH_PROJECT_ID,
                "code": "PKR-W08-JALPA-FOOTPATH-2082-83",
                "fiscal_year": fiscal_years["2082-83"],
                "title_en": "Jalpa Marg Footpath Procurement 2082/83",
                "title_np": "जाल्पा मार्ग फुटपाथ खरिद २०८२/८३",
                "description_en": (
                    "An official FY 2082/83 procurement record for footpath construction at "
                    "Jalpa Marg in Pokhara Ward 8, kept separate from the earlier road works."
                ),
                "description_np": (
                    "पोखरा वडा नं. ८ जाल्पा मार्गमा फुटपाथ निर्माणको आर्थिक वर्ष २०८२/८३ को "
                    "आधिकारिक खरिद अभिलेख, अघिल्ला सडक कार्यबाट छुट्टै राखिएको।"
                ),
                "data_note_en": (
                    "The addendum revises the estimate and deadline. Allocation, award, "
                    "contractor, payments, progress, completion, and coordinates remain unknown."
                ),
                "data_note_np": (
                    "संशोधनले अनुमान र समयसीमा परिवर्तन गर्छ। विनियोजन, ठेक्का, ठेकेदार, "
                    "भुक्तानी, प्रगति, सम्पन्नता र निर्देशाङ्क अज्ञात छन्।"
                ),
            },
        ]
        later_projects = {}
        for row in later_project_rows:
            later_project, _ = Project.objects.update_or_create(
                id=row["id"],
                defaults={
                    "code": row["code"],
                    "local_government": local_government,
                    "ward": ward,
                    "fiscal_year": row["fiscal_year"],
                    "subsector": subsector,
                    "budget_allocation": None,
                    "title_en": row["title_en"],
                    "title_np": row["title_np"],
                    "description_en": row["description_en"],
                    "description_np": row["description_np"],
                    "status": Project.Status.UNKNOWN,
                    "allocated_amount": None,
                    "official_progress_percent": None,
                    "planned_start_date": None,
                    "planned_end_date": None,
                    "data_classification": DataClassification.OFFICIAL,
                    "data_note_en": row["data_note_en"],
                    "data_note_np": row["data_note_np"],
                    "source_url": BOLPATRA_SOURCE,
                },
            )
            later_project.full_clean()
            later_project.save()
            later_projects[row["code"]] = later_project

        tender_rows = [
            {
                "project": project,
                "reference": "45/PMC/NCB/W/077-78",
                "invitation_number": "16.1/PMC/077-78",
                "title_en": "Upgrading of Jalpa Marga Road, PMC-08",
                "title_np": "जाल्पा मार्ग सडक स्तरोन्नति, पोखरा-८",
                "published_date": date(2021, 1, 28),
                "bid_submission_deadline": datetime(2021, 2, 28, 12, 0, tzinfo=NEPAL_TIMEZONE),
                "estimated_amount": Decimal("9477987.16"),
                "bid_security_amount": Decimal("270000.00"),
                "data_note_en": (
                    "Official tender estimate excluding VAT and contingencies. It is not an "
                    "awarded contract or payment amount."
                ),
                "data_note_np": (
                    "भ्याट र कन्टिन्जेन्सी बाहेकको आधिकारिक बोलपत्र अनुमान। यो प्रदान गरिएको "
                    "ठेक्का वा भुक्तानी रकम होइन।"
                ),
            },
            {
                "project": later_projects["PKR-W08-JALPA-UPGRADE-2078-79"],
                "reference": "149/PMC/NCB/W/078-079",
                "invitation_number": "57.1/PMC/078-079",
                "title_en": "Upgrading of Jalpa Marga, PMC-08",
                "title_np": "जाल्पा मार्ग स्तरोन्नति, पोखरा-८",
                "published_date": date(2022, 4, 7),
                "bid_submission_deadline": datetime(2022, 5, 8, 12, 0, tzinfo=NEPAL_TIMEZONE),
                "estimated_amount": Decimal("3282376.82"),
                "bid_security_amount": Decimal("92500.00"),
                "data_note_en": (
                    "Official tender estimate excluding VAT and including provisional sums. "
                    "No continuity with the FY 2077/78 package is assumed."
                ),
                "data_note_np": (
                    "भ्याट बाहेक र प्रोभिजनल समसहितको आधिकारिक बोलपत्र अनुमान। आर्थिक वर्ष "
                    "२०७७/७८ को प्याकेजसँग निरन्तरता मानिएको छैन।"
                ),
            },
            {
                "project": later_projects["PKR-W08-JALPA-FOOTPATH-2082-83"],
                "reference": "123/PMC/NCB/W/Purbadhar/082-83",
                "invitation_number": "34.4/PMC/082-83",
                "title_en": "Construction of Footpath at Jalpa Marga, PMC-08",
                "title_np": "जाल्पा मार्गमा फुटपाथ निर्माण, पोखरा-८",
                "published_date": date(2026, 4, 17),
                "bid_submission_deadline": datetime(2026, 6, 1, 12, 0, tzinfo=NEPAL_TIMEZONE),
                "estimated_amount": Decimal("2217190.45"),
                "bid_security_amount": Decimal("63000.00"),
                "data_note_en": (
                    "Addendum No. 1 revised the estimate from NPR 2,499,315.21 and extended "
                    "the deadline. The revised estimate excludes VAT and includes provisional sums."
                ),
                "data_note_np": (
                    "संशोधन नं. १ ले अनुमान रु. २४,९९,३१५.२१ बाट परिवर्तन गरी समयसीमा बढायो। "
                    "संशोधित अनुमान भ्याट बाहेक र प्रोभिजनल समसहित हो।"
                ),
            },
        ]
        for row in tender_rows:
            tender, _ = Tender.objects.update_or_create(
                reference=row["reference"],
                defaults={
                    "project": row["project"],
                    "invitation_number": row["invitation_number"],
                    "title_en": row["title_en"],
                    "title_np": row["title_np"],
                    "procurement_method": Tender.ProcurementMethod.OPEN,
                    "published_date": row["published_date"],
                    "bid_submission_deadline": row["bid_submission_deadline"],
                    "estimated_amount": row["estimated_amount"],
                    "bid_security_amount": row["bid_security_amount"],
                    "data_note_en": row["data_note_en"],
                    "data_note_np": row["data_note_np"],
                    "source_url": BOLPATRA_SOURCE,
                    "data_classification": DataClassification.OFFICIAL,
                },
            )
            tender.full_clean()
            tender.save()

        self.stdout.write(
            self.style.SUCCESS(f"Seeded {len(later_projects) + 1} evidence-backed Jalpa projects.")
        )
