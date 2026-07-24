from config.api import EnvelopeReadOnlyModelViewSet
from rest_framework.permissions import AllowAny

from anomalies.models import AnomalyFlag
from anomalies.serializers import AnomalyFlagSerializer


class AnomalyFlagViewSet(EnvelopeReadOnlyModelViewSet):
    serializer_class = AnomalyFlagSerializer
    permission_classes = [AllowAny]
    filterset_fields = {
        "project": ["exact"],
        "project__code": ["exact"],
        "severity": ["exact"],
        "reliability": ["exact"],
        "status": ["exact"],
        "rule_id": ["exact"],
    }
    ordering_fields = ["severity", "last_evaluated_at", "rule_id"]
    ordering = ["-severity", "rule_id"]

    def get_queryset(self):
        return AnomalyFlag.objects.select_related("project")
