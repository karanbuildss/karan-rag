from django.core.management.base import BaseCommand

from anomalies.services import evaluate_all_projects


class Command(BaseCommand):
    help = "Evaluate deterministic, explainable project anomaly rules."

    def handle(self, *args, **options):
        flags = evaluate_all_projects()
        message = f"Evaluated and activated {len(flags)} anomaly flags."
        self.stdout.write(self.style.SUCCESS(message))
