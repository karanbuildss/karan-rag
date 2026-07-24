from chat.models import ChatMessage, ChatSession
from config.api import success_response
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
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
        session_id = None
        if request.user.is_authenticated:
            with transaction.atomic():
                requested_session = query.validated_data.get("session_id")
                if requested_session:
                    session = get_object_or_404(
                        ChatSession,
                        pk=requested_session,
                        user=request.user,
                    )
                    if project and session.selected_project_id != project.id:
                        session.selected_project = project
                else:
                    session = ChatSession.objects.create(
                        user=request.user,
                        title=query.validated_data["question"][:160],
                        selected_project=project,
                    )
                ChatMessage.objects.create(
                    session=session,
                    role=ChatMessage.Role.USER,
                    content=query.validated_data["question"],
                )
                ChatMessage.objects.create(
                    session=session,
                    role=ChatMessage.Role.ASSISTANT,
                    content=result["answer"],
                    route_used=result["route"],
                    response_citations=result["citations"],
                    response_visualizations=result["visualizations"],
                )
                session.updated_at = timezone.now()
                session.save(update_fields=["selected_project", "updated_at"])
                session_id = session.id
        result["session_id"] = session_id
        output = InvestigatorResultSerializer(result)
        return success_response(output.data)
