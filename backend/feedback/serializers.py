from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from feedback.models import CitizenFeedback


class CitizenFeedbackSerializer(serializers.ModelSerializer):
    project_code = serializers.CharField(source="project.code", read_only=True)
    can_edit = serializers.SerializerMethodField()

    class Meta:
        model = CitizenFeedback
        fields = [
            "id",
            "project",
            "project_code",
            "completion_rating",
            "quality_rating",
            "usefulness_rating",
            "allocation_fairness_rating",
            "comment",
            "directly_observed",
            "is_local_resident",
            "verification_status",
            "moderation_status",
            "can_edit",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "is_local_resident",
            "verification_status",
            "moderation_status",
        ]

    @extend_schema_field(serializers.BooleanField())
    def get_can_edit(self, obj) -> bool:
        request = self.context.get("request")
        return bool(
            request
            and request.user.is_authenticated
            and obj.citizen_profile.user_id == request.user.pk
        )

    def validate(self, attrs):
        for field in (
            "completion_rating",
            "quality_rating",
            "usefulness_rating",
            "allocation_fairness_rating",
        ):
            value = attrs.get(field, getattr(self.instance, field, None))
            if value is not None and not 1 <= value <= 5:
                raise serializers.ValidationError(
                    {field: "Rating must be between 1 and 5."},
                    code="invalid_rating",
                )
        return attrs


class FeedbackAggregateSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    average_completion = serializers.DecimalField(max_digits=6, decimal_places=2, allow_null=True)
    average_quality = serializers.DecimalField(max_digits=6, decimal_places=2, allow_null=True)
    average_usefulness = serializers.DecimalField(max_digits=6, decimal_places=2, allow_null=True)
    average_allocation_fairness = serializers.DecimalField(
        max_digits=6, decimal_places=2, allow_null=True
    )


class FeedbackSummarySerializer(serializers.Serializer):
    all_citizens = FeedbackAggregateSerializer()
    verified_citizens = FeedbackAggregateSerializer()
    verified_local_residents = FeedbackAggregateSerializer()


class FeedbackSummaryResponseSerializer(serializers.Serializer):
    data = FeedbackSummarySerializer()
    meta = serializers.DictField()
    errors = serializers.ListField()
