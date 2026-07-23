from config.api import EnvelopeReadOnlyModelViewSet, success_response
from documents.models import ProjectDocumentLink
from documents.serializers import ProjectDocumentLinkSerializer
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny

from projects.models import Project
from projects.selectors import get_project_money_trail
from projects.serializers import (
    ProjectMoneyTrailResponseSerializer,
    ProjectMoneyTrailSerializer,
    ProjectSerializer,
)


class ProjectViewSet(EnvelopeReadOnlyModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [AllowAny]
    filterset_fields = {
        "local_government__code": ["exact"],
        "ward__number": ["exact"],
        "fiscal_year__code": ["exact"],
        "subsector__sector__code": ["exact"],
        "subsector__code": ["exact"],
        "status": ["exact"],
        "data_classification": ["exact"],
    }
    search_fields = [
        "code",
        "title_en",
        "title_np",
        "description_en",
        "description_np",
        "local_government__name_en",
        "local_government__name_np",
    ]
    ordering_fields = [
        "allocated_amount",
        "official_progress_percent",
        "planned_end_date",
        "title_en",
    ]
    ordering = ["title_en"]

    def get_queryset(self):
        return Project.objects.select_related(
            "local_government",
            "ward",
            "fiscal_year",
            "subsector__sector",
            "location",
        )

    @extend_schema(responses=ProjectMoneyTrailResponseSerializer)
    @action(detail=True, methods=["get"], url_path="money-trail")
    def money_trail(self, request, pk=None):
        payload = get_project_money_trail(pk)
        serializer = ProjectMoneyTrailSerializer(payload)
        return success_response(serializer.data)

    @extend_schema(responses=ProjectDocumentLinkSerializer(many=True))
    @action(detail=True, methods=["get"], url_path="evidence")
    def evidence(self, request, pk=None):
        project = self.get_object()
        links = ProjectDocumentLink.objects.filter(project=project).select_related(
            "document__local_government",
            "document__fiscal_year",
        )
        serializer = ProjectDocumentLinkSerializer(links, many=True, context={"request": request})
        return success_response(serializer.data)
