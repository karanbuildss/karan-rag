from django.core.management.base import BaseCommand, CommandError
from investigator.services.retrieval import retrieve_project_evidence
from investigator.services.routing import InvestigationRoute, QuestionLanguage
from projects.models import Project

BENCHMARK = [
    {
        "question": "How much budget was allocated to Jalpa Marg?",
        "route": InvestigationRoute.DATABASE_QUERY,
        "language": QuestionLanguage.ENGLISH,
        "relationship": "allocation",
        "page": 168,
    },
    {
        "question": "What does the audit report say about Jalpa Marg?",
        "route": InvestigationRoute.DOCUMENT_RAG,
        "language": QuestionLanguage.ENGLISH,
        "relationship": "audit",
        "page": 48,
    },
    {
        "question": "jalpa ko thekka estimate kati ho?",
        "route": InvestigationRoute.DATABASE_QUERY,
        "language": QuestionLanguage.ROMANIZED_NEPALI,
        "relationship": "procurement",
        "page": 1,
    },
    {
        "question": "45/PMC/NCB/W/077-78 ko bolpatra dekhaunuhos",
        "route": InvestigationRoute.DOCUMENT_RAG,
        "language": QuestionLanguage.ROMANIZED_NEPALI,
        "relationship": "procurement",
        "page": 1,
    },
    {
        "question": "लेखापरीक्षण प्रतिवेदनमा जाल्पा मार्गबारे के उल्लेख छ?",
        "route": InvestigationRoute.DOCUMENT_RAG,
        "language": QuestionLanguage.NEPALI,
        "relationship": "audit",
        "page": 48,
    },
]


class Command(BaseCommand):
    help = "Evaluate multilingual project evidence retrieval against known Jalpa citations."

    def add_arguments(self, parser):
        parser.add_argument("--project-code", default="PKR-W08-JALPA-2077-78")
        parser.add_argument("--fail-below", type=float, default=1.0)

    def handle(self, *args, **options):
        try:
            project = Project.objects.get(code=options["project_code"])
        except Project.DoesNotExist as exc:
            raise CommandError("Project not found.") from exc

        passed = 0
        for case_number, case in enumerate(BENCHMARK, start=1):
            citations, provider = retrieve_project_evidence(
                project,
                case["question"],
                case["route"],
                case["language"],
            )
            hit = any(
                citation["relationship"] == case["relationship"]
                and citation["page"] == case["page"]
                for citation in citations[:3]
            )
            passed += int(hit)
            status = "PASS" if hit else "FAIL"
            self.stdout.write(
                f"{status} case={case_number} language={case['language']} [{provider}] -> "
                f"{[(item['relationship'], item['page']) for item in citations[:3]]}"
            )

        score = passed / len(BENCHMARK)
        self.stdout.write(f"Retrieval hit@3: {passed}/{len(BENCHMARK)} ({score:.0%})")
        if score < options["fail_below"]:
            raise CommandError(f"Retrieval score {score:.0%} is below {options['fail_below']:.0%}.")
