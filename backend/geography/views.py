from config.api import EnvelopeReadOnlyModelViewSet
from rest_framework.permissions import AllowAny

from geography.models import LocalGovernment
from geography.serializers import LocalGovernmentSerializer


class LocalGovernmentViewSet(EnvelopeReadOnlyModelViewSet):
    serializer_class = LocalGovernmentSerializer
    permission_classes = [AllowAny]
    filterset_fields = {"code": ["exact"], "government_type": ["exact"], "district": ["exact"]}
    search_fields = ["code", "name_en", "name_np", "district__name_en", "district__name_np"]
    ordering_fields = ["code", "name_en"]
    ordering = ["name_en"]

    def get_queryset(self):
        return LocalGovernment.objects.select_related("district__province")
