from config.api import success_response
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from projects.models import Project
from rest_framework.permissions import AllowAny
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from investigator.serializers import (
    InvestigatorQuerySerializer,
    InvestigatorResponseSerializer,
    InvestigatorResultSerializer,
)
from investigator.services import investigate


class InvestigatorQueryView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "investigator"

    @extend_schema(
        request=InvestigatorQuerySerializer,
        responses=InvestigatorResponseSerializer,
        description=(
            "Route a civic question to structured project facts and page-linked evidence. "
            "Tender estimates are never treated as awards or payments."
        ),
    )
    def post(self, request):
        query = InvestigatorQuerySerializer(data=request.data)
        query.is_valid(raise_exception=True)
        project_id = query.validated_data.get("project_id")
        project = get_object_or_404(Project, pk=project_id) if project_id else None
        result = investigate(
            question=query.validated_data["question"],
            project=project,
            requested_language=query.validated_data["language"],
        )
        output = InvestigatorResultSerializer(result)
        return success_response(output.data)
