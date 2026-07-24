from accounts.models import CitizenProfile
from audit.services import record_audit
from config.api import success_response
from django.db import IntegrityError, transaction
from django.db.models import Avg, Count, Q
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from feedback.models import CitizenFeedback, FeedbackRevision
from feedback.permissions import FeedbackPermission
from feedback.serializers import CitizenFeedbackSerializer, FeedbackSummaryResponseSerializer


def _ratings_snapshot(feedback):
    return {
        "completion_rating": feedback.completion_rating,
        "quality_rating": feedback.quality_rating,
        "usefulness_rating": feedback.usefulness_rating,
        "allocation_fairness_rating": feedback.allocation_fairness_rating,
        "directly_observed": feedback.directly_observed,
    }


def _aggregate(queryset):
    values = queryset.aggregate(
        count=Count("pk"),
        average_completion=Avg("completion_rating"),
        average_quality=Avg("quality_rating"),
        average_usefulness=Avg("usefulness_rating"),
        average_allocation_fairness=Avg("allocation_fairness_rating"),
    )
    return values


class CitizenFeedbackViewSet(viewsets.ModelViewSet):
    serializer_class = CitizenFeedbackSerializer
    permission_classes = [FeedbackPermission]
    filterset_fields = {"project": ["exact"], "verification_status": ["exact"]}
    ordering = ["-updated_at"]

    def get_queryset(self):
        queryset = CitizenFeedback.objects.select_related(
            "project",
            "citizen_profile__user",
        )
        if self.request.user.is_authenticated:
            return queryset.filter(
                Q(moderation_status=CitizenFeedback.ModerationStatus.APPROVED)
                | Q(citizen_profile__user=self.request.user)
            )
        return queryset.filter(moderation_status=CitizenFeedback.ModerationStatus.APPROVED)

    def create(self, request, *args, **kwargs):
        profile, _ = CitizenProfile.objects.get_or_create(user=request.user)
        idempotency_key = request.headers.get("Idempotency-Key", "").strip() or None
        if idempotency_key and len(idempotency_key) > 64:
            return Response(
                {
                    "data": None,
                    "meta": {},
                    "errors": [
                        {
                            "code": "invalid_idempotency_key",
                            "field": None,
                            "message": "Idempotency-Key is too long.",
                        }
                    ],
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if idempotency_key:
            existing = CitizenFeedback.objects.filter(idempotency_key=idempotency_key).first()
            if existing:
                if existing.citizen_profile_id != profile.pk:
                    return Response(status=status.HTTP_409_CONFLICT)
                return success_response(self.get_serializer(existing).data)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        project = serializer.validated_data["project"]
        is_local = bool(
            profile.is_identity_verified
            and profile.verified_municipality_code == project.local_government.code
        )
        verification_status = CitizenFeedback.VerificationStatus.UNVERIFIED
        if profile.is_identity_verified:
            verification_status = (
                CitizenFeedback.VerificationStatus.VERIFIED_LOCAL
                if is_local
                else CitizenFeedback.VerificationStatus.VERIFIED
            )
        try:
            with transaction.atomic():
                feedback = serializer.save(
                    citizen_profile=profile,
                    idempotency_key=idempotency_key,
                    is_local_resident=is_local,
                    verification_status=verification_status,
                )
                record_audit(
                    actor=request.user,
                    action="feedback_created",
                    object_type="CitizenFeedback",
                    object_id=feedback.pk,
                    after=_ratings_snapshot(feedback),
                    request_identifier=request.headers.get("X-Request-ID", ""),
                )
        except IntegrityError:
            existing = CitizenFeedback.objects.filter(
                citizen_profile=profile,
                project=project,
            ).first()
            return Response(
                {
                    "data": self.get_serializer(existing).data if existing else None,
                    "meta": {},
                    "errors": [
                        {
                            "code": "duplicate_feedback",
                            "field": "project",
                            "message": (
                                "You have already rated this project. "
                                "Edit your existing rating instead."
                            ),
                        }
                    ],
                },
                status=status.HTTP_409_CONFLICT,
            )
        return success_response(
            self.get_serializer(feedback).data,
            status_code=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        feedback = self.get_object()
        before = _ratings_snapshot(feedback)
        response = super().update(request, *args, **kwargs)
        feedback.refresh_from_db()
        after = _ratings_snapshot(feedback)
        FeedbackRevision.objects.create(
            feedback=feedback,
            actor=request.user,
            before_summary=before,
            after_summary=after,
        )
        record_audit(
            actor=request.user,
            action="feedback_updated",
            object_type="CitizenFeedback",
            object_id=feedback.pk,
            before=before,
            after=after,
            request_identifier=request.headers.get("X-Request-ID", ""),
        )
        response.data = {"data": response.data, "meta": {}, "errors": []}
        return response

    @extend_schema(responses=FeedbackSummaryResponseSerializer)
    @action(detail=False, methods=["get"], url_path="summary")
    def summary(self, request):
        project_id = request.query_params.get("project")
        queryset = CitizenFeedback.objects.exclude(
            moderation_status=CitizenFeedback.ModerationStatus.REJECTED
        )
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        verified = queryset.filter(
            verification_status__in=[
                CitizenFeedback.VerificationStatus.VERIFIED,
                CitizenFeedback.VerificationStatus.VERIFIED_LOCAL,
            ]
        )
        verified_local = queryset.filter(
            verification_status=CitizenFeedback.VerificationStatus.VERIFIED_LOCAL
        )
        return success_response(
            {
                "all_citizens": _aggregate(queryset),
                "verified_citizens": _aggregate(verified),
                "verified_local_residents": _aggregate(verified_local),
            }
        )
